"""
Colombo Scanner — Case Management System
Create, list, and resume investigation cases with persistent storage.
"""
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from core.database import (
    create_case, list_cases, get_case, close_case, get_case_stats, delete_case
)

# ... (omitting top portion to directly target menu_gerenciar_cases instead via multi or exact start/end)
from core.logger import get_logger

log = get_logger("cases")
console = Console()


def selecionar_ou_criar_case() -> int:
    """
    Interactive case selection: create new or resume existing.
    Returns the case_id for the active investigation.
    """
    cases = list_cases(status="active")

    choices = [
        questionary.Choice("📁 Criar Novo Case de Investigação", value="new"),
        questionary.Choice("🔄 Sessão Rápida (sem persistência)", value="quick"),
    ]

    if cases:
        choices.insert(1, questionary.Separator("─── Cases Ativos ───"))
        for c in cases[:10]:
            stats = get_case_stats(c["id"])
            label = (
                f"📂 #{c['id']} — {c['name']} "
                f"[{stats['scan_count']} scans, {stats['entity_count']} entidades]"
            )
            choices.insert(2 + cases.index(c), questionary.Choice(label, value=c["id"]))

    escolha = questionary.select(
        "Selecione o contexto da investigação:",
        choices=choices,
        style=questionary.Style([
            ('pointer', 'fg:#00FFFF bold'),
            ('highlighted', 'fg:#00FFFF bold'),
        ])
    ).ask()

    if escolha is None:
        # User pressed Ctrl+C or Esc — fallback to quick session
        console.print("[yellow]⚠️ Seleção cancelada. Iniciando Sessão Rápida...[/yellow]")
        return create_case("Sessão Rápida", "Criada automaticamente após cancelamento")

    if escolha == "quick":
        # Quick session — create a temp case that can be discarded
        return create_case("Sessão Rápida", "Sessão sem nome — pode ser renomeada depois")

    if escolha == "new":
        nome = questionary.text(
            "Nome do Case (ex: 'Investigação Empresa X'):",
            default="Investigação"
        ).ask()
        desc = questionary.text("Descrição (opcional):", default="").ask()
        if not nome:
            nome = "Investigação"
        case_id = create_case(nome, desc or "")
        console.print(f"[bold green]✅ Case #{case_id} criado: {nome}[/bold green]")
        return case_id

    # Resuming existing case
    if isinstance(escolha, int):
        case_id = escolha
        while True:
            case = get_case(case_id)
            if not case: return selecionar_ou_criar_case()
            
            console.print(f"\n[bold cyan]📂 Opções do Case #{case['id']}: {case['name']}[/bold cyan]")
            _exibir_resumo_case(case_id)
            
            sub_acao = questionary.select(
                "O que deseja fazer?",
                choices=[
                    questionary.Choice("🚀 Começar Varredura (Entrar e Rodar)", value="enter"),
                    questionary.Choice("📖 Ver Histórico / Gerar Relatórios", value="history"),
                    questionary.Choice("⬅️ Voltar ao Menu de Seleção", value="back"),
                ]
            ).ask()
            
            if sub_acao is None or sub_acao == "enter":
                return case_id
            elif sub_acao == "history":
                _gerar_exportacao_historico_case(case_id)
            elif sub_acao == "back":
                return selecionar_ou_criar_case()

    # Fallback
    return create_case("Investigação", "")


def _exibir_resumo_case(case_id: int):
    """Shows a quick summary of the case status."""
    stats = get_case_stats(case_id)

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="cyan", justify="right")
    table.add_column(style="white")
    table.add_row("Scans realizados:", str(stats["scan_count"]))
    table.add_row("Entidades encontradas:", str(stats["entity_count"]))

    if stats["entity_types"]:
        tipo_str = ", ".join(f"{k}: {v}" for k, v in list(stats["entity_types"].items())[:5])
        table.add_row("Tipos:", tipo_str)

    console.print(Panel(table, title="[dim]Resumo do Case[/dim]", border_style="cyan"))


def menu_gerenciar_cases():
    """Menu for managing cases (list, close, view stats)."""
    cases = list_cases(status="active")
    closed_cases = list_cases(status="closed")

    table = Table(title="📁 Cases de Investigação", expand=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Nome", style="cyan")
    table.add_column("Status", width=10)
    table.add_column("Criado em", style="dim")

    for c in cases:
        table.add_row(str(c["id"]), c["name"], "[green]Ativo[/green]", c["created_at"][:16])

    for c in closed_cases[:5]:
        table.add_row(str(c["id"]), c["name"], "[dim]Fechado[/dim]", c["created_at"][:16])

    console.print(table)

    if cases or closed_cases:
        acao = questionary.select(
            "Ação:",
            choices=[
                questionary.Choice("📖 Visualizar/Exportar Histórico Completo de um Case", value="history"),
                questionary.Choice("🔒 Fechar um Case Ativo", value="close"),
                questionary.Choice("🗑️ Deletar um Case Antigo", value="delete"),
                questionary.Choice("⬅️ Voltar", value="back"),
            ]
        ).ask()

        if acao == "history":
            todos = cases + closed_cases
            opcoes = [questionary.Choice(f"#{c['id']} — {c['name']}", value=c["id"]) for c in todos]
            case_id = questionary.select("De qual Case deseja gerar o Dossiê/Visualização?", choices=opcoes).ask()
            if case_id:
                _gerar_exportacao_historico_case(case_id)

        elif acao == "close" and cases:
            opcoes = [questionary.Choice(f"#{c['id']} — {c['name']}", value=c["id"]) for c in cases]
            case_id = questionary.select("Qual case deseja fechar?", choices=opcoes).ask()
            if case_id:
                close_case(case_id)
                console.print(f"[yellow]🔒 Case #{case_id} fechado.[/yellow]")
        elif acao == "delete" and (cases or closed_cases):
            todos = cases + closed_cases
            opcoes = [questionary.Choice(f"#{c['id']} — {c['name']}", value=c["id"]) for c in todos]
            case_id = questionary.select("Qual case deseja DELETAR permanentemente?", choices=opcoes).ask()
            if case_id:
                confirm = questionary.confirm("Tem certeza que deseja deletar este case e TODOS os seus dados?").ask()
                if confirm:
                    delete_case(case_id)
                    console.print(f"[red]🗑️ Case #{case_id} deletado permanentemente.[/red]")

def _gerar_exportacao_historico_case(case_id: int):
    """Fetches all history of a case, visualizes and triggers export flow."""
    from core.database import get_raw_results_by_case
    from core.entities import ScanResult
    from core.ui import exibir_resultados
    from ui.prompts import menu_exportacao
    from core.report import gerar_relatorio
    from core.graph import gerar_grafo

    raws = get_raw_results_by_case(case_id)
    if not raws:
        console.print("[yellow]⚠️ Nenhum resultado encontrado neste Case ainda.[/yellow]")
        input("\nPressione ENTER para voltar...")
        return
        
    resultados = [ScanResult(
        plugin_name=r["plugin_name"], 
        target=r["target"], 
        raw_output=r["output"], 
        status=r["status"]
    ) for r in raws]
    
    console.print(f"\n[bold cyan]📦 Carregando {len(resultados)} resultados históricos do Case #{case_id}...[/bold cyan]")
    exibir_resultados(resultados)
    
    exports = menu_exportacao(f"Case_Completo_{case_id}")
    if exports:
        if any(x in exports for x in ["pdf", "json", "csv", "html"]):
            path = gerar_relatorio(f"Case_Completo_{case_id}", resultados)
            console.print(f"[green]✅ Relatório Completo salvo na pasta relatorios/[/green]")
        if "grafo" in exports:
            path = gerar_grafo(f"Case_Completo_{case_id}", resultados)
            console.print(f"[green]✅ Grafo do Case salvo em {path}[/green]")
    input("\nPressione ENTER para continuar...")
