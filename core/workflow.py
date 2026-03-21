from core.extractor import extract_entities
from core.runner import run_plugins_paralelo
from core.smart_scan import filtrar_plugins_smart, detectar_tipo
from rich.console import Console

console = Console()

def executar_workflow_recursivo(alvo_inicial: str, plugins_disponiveis: list, max_camadas: int = 2, verbose: bool = True) -> list:
    """
    Roda os plugins para o alvo. Extrai dados da saída. Usa esses novos dados como alvo.
    """
    resultados_totais = []
    alvos_processados = set()
    
    # Camada atual de alvos a investigar
    alvos_fila = {alvo_inicial}
    
    for camada in range(1, max_camadas + 1):
        if not alvos_fila:
            break
            
        if verbose:
            console.print(f"\n[bold blue][WORKFLOW][/bold blue] Iniciando Camada {camada} com {len(alvos_fila)} alvo(s).")
            
        alvos_camada_seguinte = set()
        
        for alvo in alvos_fila:
            if alvo in alvos_processados:
                continue
                
            alvos_processados.add(alvo)
            tipo_alvo = detectar_tipo(alvo)
            
            if verbose:
                console.print(f"[cyan]➜ Investigando:[/cyan] {alvo} ({tipo_alvo})")
                
            plugins_roda = filtrar_plugins_smart(plugins_disponiveis, alvo)
            if not plugins_roda:
                if verbose:
                    console.print(f"[dim]  Nenhum plugin útil para {alvo}[/dim]")
                continue
                
            res = run_plugins_paralelo(plugins_roda, {"alvo": alvo})
            
            # Formatar para o relatório final adicionando tracking
            for r in res:
                r["alvo_origem"] = alvo
                r["camada"] = camada
            
            resultados_totais.extend(res)
            
            # Extração de novos alvos (apenas se não for a última camada)
            if camada < max_camadas:
                if verbose:
                    console.print(f"  [dim]Extraindo novas pistas dos {len(res)} resultados de {alvo}...[/dim]")
                    
                novas_pistas = 0
                for r in res:
                    extraido = extract_entities(r.get("output", ""))
                    for tipo, pistas in extraido.items():
                        for p in pistas:
                            if p not in alvos_processados and len(p) > 3:
                                alvos_camada_seguinte.add(p)
                                novas_pistas += 1
                                
                if verbose and novas_pistas > 0:
                    console.print(f"  [bold green]✓ Encontradas {novas_pistas} novas pistas relacionadas a {alvo}![/bold green]")
                    
        # Define a nova fila
        alvos_fila = alvos_camada_seguinte
        
    if verbose:
        console.print(f"\n[bold blue][WORKFLOW][/bold blue] Finalizado! Total de alvos únicos investigados: {len(alvos_processados)}")
        
    return resultados_totais
