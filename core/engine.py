from typing import Optional, List, Dict, Any
from core.plugin_manager import load_plugins
from core.runner import run_plugins_paralelo, run_plugin
from core.smart_scan import filtrar_plugins_smart, detectar_tipo
from core.workflow import executar_workflow_recursivo
from core.intelligence import extrair_insights, extrair_entidades
from core.database import create_scan, finish_scan, save_raw_result, save_entities, get_case
from core.notifications import notificar_scan_completo
from core.logger import get_logger
from core.entities import ScanResult

log = get_logger("engine")

class ColomboEngine:
    def __init__(self):
        self.plugins = load_plugins()

    def run_direct_scan(self, alvo: str, case_id: int = None, selected_plugins: list = None) -> list[ScanResult]:
        """Executes a direct scan on a target."""
        if not selected_plugins:
            selected_plugins = filtrar_plugins_smart(self.plugins, alvo)
            
        if not selected_plugins:
            return []

        inputs = {"alvo": alvo}
        resultados = run_plugins_paralelo(selected_plugins, inputs)
        
        if case_id:
            self.persistir_resultados(case_id, alvo, resultados, scan_type="direct")
        
        return resultados

    def run_workflow_scan(self, alvo: str, case_id: int = None, layers: int = 2, category: str = "all", verbose: bool = True) -> list[ScanResult]:
        """Executes a recursive workflow scan."""
        plugins_ativos = self.plugins
        if category != "all":
            plugins_ativos = [p for p in self.plugins if p.get("category") == category]

        resultados = executar_workflow_recursivo(alvo, plugins_ativos, max_camadas=layers, verbose=verbose)
        
        if case_id:
            self.persistir_resultados(case_id, alvo, resultados, scan_type="workflow")
        
        return resultados

    def run_multi_target_scan(self, alvos: list[str], case_id: int = None, aprofundar: bool = False, layers: int = 1) -> list[ScanResult]:
        """Investigação Automática: processa VÁRIOS alvos de tipos diferentes.
        Se aprofundar=True, usa workflow recursivo para cada alvo."""
        todos_resultados: list[ScanResult] = []

        for alvo in alvos:
            if aprofundar:
                resultados = executar_workflow_recursivo(alvo, self.plugins, max_camadas=layers, verbose=True)
                todos_resultados.extend(resultados)
            else:
                plugins = filtrar_plugins_smart(self.plugins, alvo)
                if plugins:
                    resultados = run_plugins_paralelo(plugins, {"alvo": alvo})
                    todos_resultados.extend(resultados)

        if case_id:
            alvo_principal = alvos[0] if alvos else "multi"
            self.persistir_resultados(case_id, alvo_principal, todos_resultados, scan_type="automatica")

        return todos_resultados

    def get_alvos_info(self, alvos: list[str]) -> list[tuple[str, str, int]]:
        """Retorna [(alvo, tipo_detectado, num_ferramentas)] para preview."""
        info = []
        for alvo in alvos:
            tipo = detectar_tipo(alvo)
            n_tools = len(filtrar_plugins_smart(self.plugins, alvo))
            info.append((alvo, tipo, n_tools))
        return info

    def run_manual_scan(self, plugins: list, inputs: dict, case_id: int = None) -> list[ScanResult]:
        """Executes selected plugins with specific inputs."""
        resultados = run_plugins_paralelo(plugins, inputs)
        
        if case_id:
            alvo = inputs.get("alvo", "manual_scan")
            self.persistir_resultados(case_id, alvo, resultados, scan_type="manual")
            
        return resultados

    def persistir_resultados(self, case_id: int, alvo: str, resultados: list[ScanResult], scan_type: str) -> Optional[int]:
        """Helper to save results to DB and trigger notifications."""
        if not resultados:
            log.warning(f"Engine: Nenhum resultado para persistir em {alvo}")
            return None

        scan_id = None
        try:
            scan_id = create_scan(case_id, alvo, scan_type=scan_type, plugin_count=len(resultados))
            if not scan_id:
                raise RuntimeError("Falha ao criar registro de Scan no banco.")

            all_entities = []
            
            for r in resultados:
                try:
                    save_raw_result(
                        scan_id=scan_id,
                        plugin_name=r.plugin_name,
                        target=alvo,
                        output=r.raw_output,
                        layer=r.layer
                    )
                    entities = extrair_entidades(r.raw_output, source_tool=r.plugin_name, source_target=alvo)
                    all_entities.extend(entities)
                except Exception as e:
                    log.error(f"Erro ao salvar resultado individual ({r.plugin_name}): {e}")

            if all_entities:
                try:
                    save_entities(case_id, scan_id, all_entities)
                except Exception as e:
                    log.error(f"Erro ao salvar entidades correlacionadas: {e}")
            
            finish_scan(scan_id, status="completed")
            log.info(f"Scan {scan_id} finalizado e persistido com sucesso.")

            # Notifications (non-blocking)
            try:
                case = get_case(case_id)
                insights = extrair_insights(resultados)
                notificar_scan_completo(
                    alvo=alvo,
                    total_plugins=len(resultados),
                    total_entidades=len(all_entities),
                    case_name=case.get("name", "") if case else "Case",
                    correlacoes=len(insights.get("correlacoes", []))
                )
            except Exception as e:
                log.warning(f"Falha ao enviar notificação: {e}")

            return scan_id

        except Exception as e:
            log.error(f"Erro crítico na persistência do Engine: {e}")
            if scan_id:
                try:
                    finish_scan(scan_id, status="failed")
                except:
                    pass
            return None
