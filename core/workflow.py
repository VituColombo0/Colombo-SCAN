"""
Colombo Scanner — Recursive Workflow Engine
Runs plugins for a target, extracts new leads from output, and investigates recursively.
Enhanced with entity extraction and persistence.
"""
from core.runner import run_plugins_paralelo
from core.smart_scan import filtrar_plugins_smart, detectar_tipo
from core.intelligence import extrair_entidades
from core.logger import get_logger
from rich.console import Console

log = get_logger("workflow")
console = Console()

MAX_LEADS_PER_LAYER = 20  # Limite de novas pistas por camada para evitar explosão

from core.entities import ScanResult, EntityType

def executar_workflow_recursivo(alvo_inicial: str, plugins_disponiveis: list,
                                 max_camadas: int = 2, verbose: bool = True) -> list[ScanResult]:
    """
    Runs plugins for the target. Extracts new leads from output.
    Uses those leads as new targets recursively up to max_camadas depth.
    """
    resultados_totais: list[ScanResult] = []
    alvos_processados = set()
    alvos_fila = {alvo_inicial: ("Manual/Arquivo", "Input Inicial")}  # Dict: alvo -> (source_tool, source_target)

    for camada in range(1, max_camadas + 1):
        if not alvos_fila:
            break

        if verbose:
            console.print(f"\n[bold blue][WORKFLOW][/bold blue] Iniciando Camada {camada} com {len(alvos_fila)} alvo(s).")

        alvos_camada_seguinte = {}  # type: dict[str, tuple[str, str]]
        leads_count = 0

        for alvo, source_info in alvos_fila.items():
            if alvo in alvos_processados:
                continue

            alvos_processados.add(alvo)
            tipo_alvo = detectar_tipo(alvo)

            if verbose:
                if source_info[0] == "Manual/Arquivo":
                    console.print(f"[cyan]➜ Investigando:[/cyan] {alvo} ({tipo_alvo})")
                else:
                    console.print(f"[cyan]➜ Investigando:[/cyan] {alvo} ({tipo_alvo}) [dim](Encontrado via {source_info[0]} em {source_info[1]})[/dim]")

            plugins_roda = filtrar_plugins_smart(plugins_disponiveis, alvo)
            if not plugins_roda:
                continue

            # Pass 'camada' in inputs so ScanResult captures it
            res = run_plugins_paralelo(plugins_roda, {"alvo": alvo, "camada": camada})
            resultados_totais.extend(res)

            # Extract new leads
            if camada < max_camadas and leads_count < MAX_LEADS_PER_LAYER:
                novas_pistas_alvo = 0
                for r in res:
                    output = r.raw_output
                    if not output: continue

                    entities = extrair_entidades(output, source_tool=r.plugin_name, source_target=alvo)
                    for e in entities:
                        if e.type not in [EntityType.EMAIL, EntityType.IP, EntityType.DOMAIN, EntityType.PHONE, EntityType.USERNAME]:
                            continue
                            
                        val = e.value
                        if val not in alvos_processados and val not in alvos_camada_seguinte and len(val) > 3:
                            if leads_count < MAX_LEADS_PER_LAYER:
                                alvos_camada_seguinte[val] = (r.plugin_name, alvo)
                                novas_pistas_alvo += 1
                                leads_count += 1

                if verbose and novas_pistas_alvo > 0:
                    console.print(f"  [bold green]✓ Encontradas {novas_pistas_alvo} novas pistas relacionadas a {alvo}![/bold green]")

            if leads_count >= MAX_LEADS_PER_LAYER and verbose:
                # Optional warning...
                pass

        alvos_fila = alvos_camada_seguinte

    if verbose:
        console.print(f"\n[bold blue][WORKFLOW][/bold blue] Finalizado! Total de alvos únicos investigados: {len(alvos_processados)}")

    return resultados_totais
