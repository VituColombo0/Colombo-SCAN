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
    """Renders the styled dashboard header with real Docker status (cached)."""
    docker_display = _get_docker_status()

    stats = Table.grid(padding=(0, 1))
    stats.add_column(style="cyan", justify="right")
    stats.add_column(style="white")
    stats.add_row("OS:", f"{platform.system()} {platform.release()}")
    stats.add_row("Python:", sys.version.split()[0])
    stats.add_row("Plugins:", f"[bold green]{plugin_count}[/bold green] ativos")
    stats.add_row("Docker:", docker_display)

    heart = "".join(random.choice(["❤️", "💙", "💚", "💛"]) for _ in range(3))
    stats.add_row("Heartbeat:", heart)

    banner_text = "[bold blue]C O L O M B O[/bold blue] [bold white]S C A N N E R[/bold white]"
    tagline = "[dim italic]Advanced OSINT Intelligence Platform[/dim italic]"

    console.print(Panel(
        Columns([
            Panel(banner_text + "\n" + tagline, border_style="blue", padding=(1, 2)),
            Panel(stats, title="[dim]Status[/dim]", border_style="cyan")
        ]),
        border_style="magenta",
        title="[bold white]V4.1 TERMINAL PRO[/bold white]"
    ))


def exibir_tutorial():
    """Shows the operational manual styled panels."""
    man_auto = (
        "[bold cyan]🎯 Investigação Automática[/bold cyan]\n"
        "Junta o melhor dos dois mundos. Você cola os dados (um ou vários, "
        "em qualquer formato), e o sistema detecta os tipos e roda as ferramentas corretas.\n"
        "Você também pode escolher 'aprofundar' (Workflow), onde o sistema pega tudo novo que achou "
        "e investiga automaticamente em sucessivas camadas."
    )
    man_manual = (
        "[bold green]🧩 Modo Manual[/bold green]\n"
        "Acesso total ao nosso arsenal de ferramentas organizadas por categoria. "
        "Use para investigações cirúrgicas em infraestrutura, redes sociais ou dark web.\n"
        "Use '🔥 Executar Todas' para rodar todas as ferramentas de uma vez.\n"
        "[dim]Dica: O Smart Parser aceita qualquer formato de dado![/dim]"
    )

    console.print(Panel(
        Columns([
            Panel(man_auto, title="1. Auto-Investigador", border_style="cyan", width=40),
            Panel(man_manual, title="2. Controle Manual", border_style="green", width=40),
        ]),
        title="📚 Manual Operacional", border_style="blue"
    ))
    input("\nPressione ENTER para voltar ao menu...")


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
