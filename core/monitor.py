"""
Colombo Scanner — Continuous Monitoring Engine (Watchdog)
Periodic execution and differential alerting.
"""
import time
from datetime import datetime
from rich.console import Console
from core.database import get_case, get_new_entities_diff
from core.notifications import notificar_alerta_monitoramento
from core.logger import get_logger

log = get_logger("monitor")
console = Console()

def formatar_detalhes_entidades(entidades: list[dict]) -> str:
    """Formats a preview of the newest found entities."""
    if not entidades:
        return "Nenhuma pista relevante identificada."
    
    # Group by type and count
    from collections import Counter
    contagem = Counter(e['type'] for e in entidades)
    resumo = ", ".join(f"{cnt} {tipo}(s)" for tipo, cnt in contagem.items())
    
    # Show up to 5 examples
    exemplos = "\n".join(f"- {e['type']}: {e['value']} (via {e['source_tool']})" for e in entidades[:5])
    if len(entidades) > 5:
        exemplos += f"\n... e mais {len(entidades) - 5} outras pistas registradas no banco."
        
    return f"**Resumo**: {resumo}\n**Exemplos**:\n{exemplos}"


def iniciar_monitoramento(alvo: str, plugins: list, case_id: int, intervalo_horas: float = 24.0):
    """
    Runs a continuous watchdog loop for the target.
    Delegates the scan to main.py's _persistir_resultados.
    """
    if not isinstance(intervalo_horas, (int, float)) or intervalo_horas <= 0:
        intervalo_horas = 24.0
    from core.smart_scan import filtrar_plugins_smart
    from core.runner import run_plugins_paralelo
    import main

    case = get_case(case_id)
    case_name = case.get("name", f"Case #{case_id}") if case else "Desconhecido"

    console.print()
    console.print("[bold red]🚨 INICIANDO MODO CÃO DE GUARDA 🚨[/bold red]")
    console.print(f"🎯 Alvo: [cyan]{alvo}[/cyan]")
    console.print(f"📂 Case: [yellow]{case_name}[/yellow]")
    console.print(f"⏰ Intervalo: [magenta]A cada {intervalo_horas} horas[/magenta]")
    console.print("[dim]Pressione Ctrl+C para interromper o monitoramento a qualquer momento.[/dim]\n")
    
    intervalo_segundos = intervalo_horas * 3600
    ciclo = 1

    while True:
        try:
            start_time = datetime.now()
            console.print(f"[bold blue]🔄 Iniciando Ciclo {ciclo} ({start_time.strftime('%Y-%m-%d %H:%M:%S')})[/bold blue]")
            
            # Executar varredura
            plugins_roda = filtrar_plugins_smart(plugins, alvo)
            if not plugins_roda:
                log.warning(f"Sem plugins recomendados para monitorar {alvo}.")
                console.print(f"[red]Erro: Nenhum plugin útil para processar o alvo '{alvo}'. Encerrando.[/red]")
                return
                
            resultados = run_plugins_paralelo(plugins_roda, {"alvo": alvo})
            
            # Persistir e pegar o novo scan_id
            scan_id = main._persistir_resultados(case_id, alvo, resultados, scan_type="monitor")
            
            if not scan_id:
                console.print("[red]Erro: Não foi possível obter scan_id devido a um problema no banco.[/red]")
                time.sleep(intervalo_segundos)
                continue

            # Verificar diff
            novas_entidades = get_new_entities_diff(case_id, scan_id)
            qtd_novas = len(novas_entidades)
            
            if qtd_novas > 0:
                console.print(f"[bold green]🔔 ALERTA: Foram descobertas {qtd_novas} novas pistas neste ciclo![/bold green]")
                detalhes = formatar_detalhes_entidades(novas_entidades)
                notificar_alerta_monitoramento(alvo, case_name, qtd_novas, detalhes)
                log.info(f"Ciclo {ciclo}: {qtd_novas} novas entidades encontradas e notificadas.")
            else:
                console.print(f"[dim]✓ Ciclo {ciclo} finalizado. Nenhuma pista nova vista.[/dim]")
                log.info(f"Ciclo {ciclo}: Nenhuma novidade no alvo {alvo}.")

            # Wait for next cycle
            ciclo += 1
            console.print(f"[dim]💤 Aguardando {intervalo_horas} horas até a próxima checagem...[/dim]\n")
            time.sleep(intervalo_segundos)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]🛑 Monitoramento Cão de Guarda encerrado pelo usuário.[/bold yellow]")
            break
        except Exception as e:
            log.error(f"Erro inesperado no monitoramento (Ciclo {ciclo}): {e}")
            console.print(f"[red]Erro crítico durante o monitoramento: {e}[/red]")
            console.print(f"[dim]Tentando novamente em {intervalo_horas} horas...[/dim]")
            time.sleep(intervalo_segundos)
