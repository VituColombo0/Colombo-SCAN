"""
Colombo Scanner v4.1 — Visual Components
Banner, tutorial e formatação clássica.
"""
import sys
import platform
import random
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

_cached_docker_status = None

def _get_docker_status():
    """Cached Docker status to avoid blocking on every banner render."""
    global _cached_docker_status
    if _cached_docker_status is not None:
        return _cached_docker_status
    try:
        from core.health_check import check_dependencies, format_status_for_banner
        dep_status = check_dependencies()
        _cached_docker_status = format_status_for_banner(dep_status)
    except Exception:
        _cached_docker_status = "[dim]? (não verificado)[/dim]"
    return _cached_docker_status

def print_banner(plugin_count: int = 0):
    """Renders a high-tech premium dashboard header."""
    docker_display = _get_docker_status()
    
    # Header layout
    banner_text = Text.from_markup("[bold blue]C O L O M B O[/bold blue] [bold white]S C A N N E R[/bold white]")
    tagline = Text.from_markup("[dim italic]The Ultimate Professional OSINT & Intelligence Framework[/dim italic]")
    
    # Stats table
    stats = Table.grid(padding=(0, 2))
    stats.add_column(style="bright_black", justify="right")
    stats.add_column(style="bright_blue")
    
    stats.add_row("AGENT ID:", f"ANTIGRAVITY-PRO")
    stats.add_row("CORE RELEASE:", f"v4.2.0-Lethal")
    stats.add_row("DOCKER ENGINE:", docker_display)
    stats.add_row("LOADED PLUGINS:", f"[bold white]{plugin_count}[/bold white]")
    
    # Build the main panel
    header_content = Table.grid(expand=True)
    header_content.add_column(ratio=2)
    header_content.add_column(ratio=1)
    
    header_content.add_row(
        Panel(Text.assemble(banner_text, "\n", tagline), border_style="blue", padding=(1, 2)),
        Panel(stats, title="[dim]SECURITY STATUS[/dim]", border_style="bright_black")
    )
    
    console.print(Panel(
        header_content,
        border_style="bright_blue",
        title="[bold yellow]⚡ HIGH PRIORITY OPERATIONAL DASHBOARD ⚡[/bold yellow]",
        subtitle="[dim]RESTRICTED ACCESS — OSINT CLEARANCE REQUIRED[/dim]"
    ))
    console.print()

def create_live_scan_dashboard(target: str, plugin_name: str, status: str = "In Progress"):
    """Creates a temporary dashboard fragment for live scan feedback."""
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_row(f"[bold white]Targeting:[/bold white] [cyan]{target}[/cyan]")
    grid.add_row(f"[bold white]Executing:[/bold white] [yellow]{plugin_name}[/yellow]")
    grid.add_row(f"[bold white]Status:[/bold white] [green]{status}[/green]")
    
    return Panel(grid, title="[bold red]LIVE EXECUTION[/bold red]", border_style="red")


def exibir_tutorial():
    """Shows the operational manual styled panels."""
    man_auto = (
        "[bold cyan]🎯 AUTO-INVESTIGATOR (SMART MODE)[/bold cyan]\n"
        "Advanced heuristic engine. Paste any data format (phone, email, IP, "
        "CNPJ, etc.), and the system will auto-detect and deploy relevant tools.\n\n"
        "[bold white]Deep Dive (Workflow):[/bold white] Enables recursive scanning. "
        "Automatically pivots on discovered leads across multiple layers."
    )
    man_manual = (
        "[bold green]🧩 TACTICAL CONTROL (MANUAL MODE)[/bold green]\n"
        "Full access to the tactical toolset organized by intelligence category. "
        "Perfect for surgical strikes on infrastructure or specific personas.\n\n"
        "[bold white]Lethal Mode:[/bold white] Use '🔥 Executar Todas' to deploy the entire "
        "category arsenal against the target simultaneously."
    )

    console.print(Panel(
        Columns([
            Panel(man_auto, title="01 — AUTO ENGINE", border_style="cyan", width=45),
            Panel(man_manual, title="02 — MANUAL CONTROL", border_style="green", width=45),
        ]),
        title="[bold white]📚 OPERATIONAL FIELD MANUAL[/bold white]", 
        border_style="bright_blue",
        padding=(1, 1)
    ))
    input("\n[dim]Press ENTER to return to base...[/dim]")


def formatar_saida_terminal(texto: str) -> str:
    """Formats raw tool output for terminal display with truncation."""
    if not texto:
        return "[italic dim]Nenhum dado retornado pela ferramenta.[/italic dim]"

    # Detect HTML response (likely WAF/captcha block)
    if ("<html" in texto.lower() or "<!doctype" in texto.lower()) and len(texto) > 1000:
        texto = "⚠️ [Aviso] A ferramenta retornou uma página HTML inteira (possível bloqueio via Captcha/WAF).\n" + texto

    linhas = [l for l in texto.split("\n") if l.strip()]
    novas_linhas = []

    for l in linhas:
        if len(l) > 150:
            novas_linhas.append(l[:150] + "... [✂️ linha truncada]")
        else:
            novas_linhas.append(l)

    if len(novas_linhas) > 30:
        truncado = (
            "\n".join(novas_linhas[:15]) +
            f"\n\n... ✂️ [Log imenso ocultado visualmente ({len(novas_linhas)} linhas totais). "
            "Verifique o Relatório para o dado completo] ✂️ ...\n\n" +
            "\n".join(novas_linhas[-5:])
        )
        return truncado

    return "\n".join(novas_linhas)
