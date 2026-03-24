"""
Colombo Scanner — UI Module
All terminal presentation functions (banner, tutorial, result formatting)
extracted from main.py for clean separation of concerns.
"""
import sys
import platform
import random

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from core.entities import ScanResult

from core.intelligence import extrair_insights, exibir_dashboard_inteligencia

console = Console()


def print_banner(plugin_count: int = 0):
    """Renders the styled dashboard header with system stats."""
    print("\033c", end="")

    stats = Table.grid(padding=(0, 1))
    stats.add_column(style="cyan", justify="right")
    stats.add_column(style="white")
    stats.add_row("System:", f"{platform.system()} {platform.release()}")
    stats.add_row("Python:", sys.version.split()[0])
    stats.add_row("Plugins:", f"[bold green]{plugin_count}[/bold green] Ativos")
    stats.add_row("Docker:", "[bold sky_blue1]Connected[/bold sky_blue1]")

    heart = "".join(random.choice(["❤️", "💙", "💚", "💛"]) for _ in range(3))
    stats.add_row("Heartbeat:", heart)

    banner_text = "[bold blue]C O L O M B O[/bold blue] [bold white]S C A N N E R[/bold white]"
    tagline = "[dim italic]Advanced OSINT Intelligence Platform[/dim italic]"

    header_content = Panel(
        Columns([
            Panel(banner_text + "\n" + tagline, border_style="blue", padding=(1, 2)),
            Panel(stats, title="[dim]Status[/dim]", border_style="cyan")
        ]),
        border_style="magenta",
        title="[bold white]V3.0 HARDENED EDITION[/bold white]"
    )
    console.print(header_content)


def exibir_tutorial():
    """Shows the operational manual in a styled panel layout."""
    man_direto = (
        "[bold cyan]🎯 Varredura Direta[/bold cyan]\n"
        "Ideal para quando você tem um alvo único (ex: 'vitu@email.com') e quer "
        "resultados rápidos sem configurar nada. O sistema detecta o tipo de dado "
        "e ativa as melhores ferramentas em paralelo."
    )
    man_manual = (
        "[bold green]🧩 Modo Manual[/bold green]\n"
        "Acesso total ao nosso arsenal de mais de 100 ferramentas organizadas por categoria. "
        "Use para investigações cirúrgicas em infraestrutura, redes sociais, dark web ou "
        "forense de imagens."
    )
    man_workflow = (
        "[bold magenta]🕵️ Workflow Agente[/bold magenta]\n"
        "O 'Modo Deus' do Colombo. Você dá um alvo inicial e o sistema minera recursivamente "
        "novas informações. Ex: Acha um email -> Busca o email -> Acha um username -> Busca o username."
    )
    man_intel = (
        "[bold yellow]🧠 Cérebro (Correlação)[/bold yellow]\n"
        "O sistema correlaciona resultados automaticamente. Se o mesmo email aparecer em "
        "ferramentas diferentes, ele será destaque no Painel de Insights com scoring."
    )
    man_cases = (
        "[bold red]📂 Cases (Persistência)[/bold red]\n"
        "Cada investigação é salva em um Case no banco de dados local. "
        "Retome investigações anteriores, compare resultados históricos."
    )

    console.print(Panel(
        Columns([
            Panel(man_direto, title="1. Agilidade", border_style="cyan"),
            Panel(man_manual, title="2. Controle", border_style="green")
        ]),
        title="📚 Manual Operacional - Parte 1", border_style="blue"
    ))
    console.print(Panel(
        Columns([
            Panel(man_workflow, title="3. Autonomia", border_style="magenta"),
            Panel(man_intel, title="4. Inteligência", border_style="yellow")
        ]),
        title="📚 Manual Operacional - Parte 2", border_style="blue"
    ))
    console.print(Panel(
        Panel(man_cases, title="5. Persistência", border_style="red"),
        title="📚 Manual Operacional - Parte 3", border_style="blue"
    ))


def formatar_saida_terminal(texto: str) -> str:
    """Formats raw tool output for terminal display with truncation."""
    if not texto:
        return "[italic dim]Nenhum dado retornado pela ferramenta.[/italic dim]"

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
            "Verifique o Relatório Markdown/CSV para o dado completo] ✂️ ...\n\n" +
            "\n".join(novas_linhas[-5:])
        )
        return truncado

    return "\n".join(novas_linhas)


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
