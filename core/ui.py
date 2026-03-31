"""
Colombo_SCAN — UI Module (Result Display)
Result formatting and intelligence dashboard display.
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from core.entities import ScanResult
from ui.components import formatar_saida_terminal

console = Console()


def exibir_resultados(resultados: list[ScanResult]):
    """Displays formatted scan results with a premium tactical dashboard."""
    from core.intelligence import extrair_insights, exibir_dashboard_inteligencia
    from rich.rule import Rule
    
    # Header Rule
    console.print(Rule("[bold red]MISSION INTEL DATA STREAM[/bold red]", style="bright_black"))
    console.print()

    insights = extrair_insights(resultados)
    exibir_dashboard_inteligencia(insights)

    for r in resultados:
        saida = r.raw_output
        if not saida:
            saida = "[dim italic]NO DATA RETURNED OR ENGINE ERROR.[/dim italic]"

        # Create a more structured result box
        meta_table = Table.grid(expand=True)
        meta_table.add_column(style="bright_black", justify="left")
        meta_table.add_column(style="bright_blue", justify="right")
        meta_table.add_row(
            f"EXEC_TIME: {r.execution_time:.2f}s",
            f"LAYER: {r.layer}"
        )

        content = formatar_saida_terminal(str(saida))
        
        result_content = Table.grid(expand=True)
        result_content.add_row(content)
        result_content.add_row(Rule(style="dim bright_black"))
        result_content.add_row(meta_table)

        painel = Panel(
            result_content,
            title=f"[white]🛰️ ASSET OUTPUT: [bold cyan]{r.plugin_name.upper()}[/bold cyan]",
            border_style="bright_blue",
            padding=(1, 2)
        )
        console.print(painel)
        console.print()
    
    console.print(Rule("[bold green]END OF INTEL STREAM[/bold green]", style="bright_black"))
    console.print()
