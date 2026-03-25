"""
Colombo Scanner — UI Module (Result Display)
Result formatting and intelligence dashboard display.
"""
from rich.console import Console
from rich.panel import Panel
from core.entities import ScanResult
from ui.components import formatar_saida_terminal

console = Console()


def exibir_resultados(resultados: list[ScanResult]):
    """Displays formatted scan results with intelligence dashboard."""
    from core.intelligence import extrair_insights, exibir_dashboard_inteligencia
    insights = extrair_insights(resultados)
    exibir_dashboard_inteligencia(insights)

    for r in resultados:
        saida = r.raw_output
        if not saida:
            saida = "[dim italic]Nenhum dado retornado ou erro no plugin.[/dim italic]"

        painel = Panel(
            formatar_saida_terminal(str(saida)),
            title=f"[white]🔍 Resultado: [bold cyan]{r.plugin_name}[/bold cyan]",
            border_style="blue",
            subtitle=f"[dim]Time: {r.execution_time:.2f}s | Layer: {r.layer}[/dim]"
        )
        console.print(painel)
        console.print()
