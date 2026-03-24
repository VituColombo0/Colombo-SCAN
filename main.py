"""
Colombo Scanner — Main Entry Point (v3.0 Hardened Edition)
Clean entrypoint that delegates all logic to core modules.
"""
import argparse
import sys

import questionary
from rich.console import Console

from core.plugin_manager import load_plugins
from core.runner import run_plugins_paralelo, run_plugin
from core.smart_scan import filtrar_plugins_smart, detectar_tipo, categorias_recomendadas
from core.report import gerar_relatorio
from core.graph import gerar_grafo
from core.health_check import check_dependencies, format_status_for_banner
from core.workflow import executar_workflow_recursivo
from core.intelligence import extrair_insights, exibir_dashboard_inteligencia, extrair_entidades
from core.ui import (
    print_banner, exibir_tutorial, formatar_saida_terminal, exibir_resultados, console
)
from core.cases import selecionar_ou_criar_case, menu_gerenciar_cases
from core.database import (
    create_scan, finish_scan, save_raw_result, save_entities,
    get_case, get_case_stats
)
from core.notifications import notificar_scan_completo
from core.entities import Entity
from core.logger import get_logger

log = get_logger("main")


def modo_silencioso(alvo: str, categoria: str = None, paralelo: bool = True):
    """
    Non-interactive mode: colombo --alvo email@x.com --cat '📧 Análise de Emails'
    Useful for scripting and automation.
    """
    plugins = load_plugins()

    if categoria:
        plugins_rodar = [p for p in plugins if p.get("category") == categoria]
    else:
        plugins_rodar = filtrar_plugins_smart(plugins, alvo)

    if not plugins_rodar:
        console.print(f"[red]Nenhum plugin encontrado para o alvo: {alvo}[/red]")
        sys.exit(1)

    tipo = detectar_tipo(alvo)
    console.print(f"[cyan]Alvo: {alvo} | Tipo: {tipo} | Plugins: {len(plugins_rodar)}[/cyan]\n")

    inputs = {"alvo": alvo}

    if paralelo:
        resultados = run_plugins_paralelo(plugins_rodar, inputs)
    else:
        resultados = [{"name": p["name"], "output": run_plugin(p, inputs)} for p in plugins_rodar]

    exibir_resultados(resultados)

    caminho = gerar_relatorio(alvo, resultados)
    console.print(f"\n[bold green]✅ Relatório: {caminho}[/bold green]")
    return resultados


def processar_exportacoes(alvo: str, resultados: list):
    """Handles report export after scan completion."""
    if not resultados:
        return

    opcoes_export = questionary.checkbox(
        "O que quer exportar?",
        choices=[
            questionary.Choice("📄 Relatório PDF", checked=True),
            questionary.Choice("🔗 Grafo de Links (HTML interativo)", checked=True)
        ]
    ).ask()

    if not opcoes_export:
        return

    if "📄 Relatório PDF" in opcoes_export:
        caminho = gerar_relatorio(alvo, resultados)
        console.print(f"\n[bold green]✅ PDF: {caminho}[/bold green]")

    if "🔗 Grafo de Links (HTML interativo)" in opcoes_export:
        caminho_grafo = gerar_grafo(alvo, resultados)
        console.print(f"[bold green]✅ Grafo: {caminho_grafo}[/bold green]\n")


def modo_workflow(alvo: str, plugins: list, case_id: int = None):
    """Workflow mode — recursive investigation across layers."""
    from rich.panel import Panel

    console.print(Panel(
        "[italic]O Workflow pegará a saída do seu alvo inicial e vai minerar novas informações.\n"
        "O número de 'Camadas' define o quão fundo na toca do coelho o scanner deve ir.[/italic]",
        border_style="magenta", title="🕵️ Modo Operador de Inteligência"
    ))

    cats_vivas = sorted(list(set(p.get("category", "Outros") for p in plugins)))
    opcoes_cat = [questionary.Choice(f"Utilizar TODAS as Ferramentas ({len(plugins)})", value="all")]
    opcoes_cat += [questionary.Choice(c, value=c) for c in cats_vivas]

    cat_filtro = questionary.select(
        "Deseja restringir o Agente a quais categorias?",
        choices=opcoes_cat
    ).ask()

    plugins_ativos = plugins
    if cat_filtro != "all":
        plugins_ativos = [p for p in plugins if p.get("category") == cat_filtro]
        console.print(f"[yellow]⚠️ Agente restringido a: [bold]{cat_filtro}[/bold] ({len(plugins_ativos)} ferramentas)[/yellow]")

    verbose = questionary.confirm("Ativar Modo Explicativo (Pensamento do Agente)?", default=True).ask()
    try:
        camadas = int(questionary.text("Camadas de profundidade (1-5):", default="2").ask())
    except ValueError:
        camadas = 2

    resultados = executar_workflow_recursivo(alvo, plugins_ativos, max_camadas=camadas, verbose=verbose)
    exibir_resultados(resultados)

    # Persist results if case is active
    if case_id:
        _persistir_resultados(case_id, alvo, resultados, scan_type="workflow")

    return resultados


def modo_direto(alvo: str, plugins: list, case_id: int = None):
    """Direct scan mode — auto-detect target type and run recommended tools."""
    from rich.panel import Panel

    tipo = detectar_tipo(alvo)
    cats = categorias_recomendadas(alvo)
    console.print(Panel(
        f"Target: [bold]{alvo}[/bold]\n"
        f"Tipo detectado: [bold yellow]{tipo}[/bold yellow]\n"
        f"Categorias: [cyan]{', '.join(cats)}[/cyan]",
        title="Análise Preliminar", border_style="blue"
    ))

    plugins_smart = filtrar_plugins_smart(plugins, alvo)
    if not plugins_smart:
        console.print("[yellow]Nenhum plugin encontrado para esse tipo.[/yellow]")
        return []

    acao = questionary.select(
        f"Foram encontradas {len(plugins_smart)} ferramentas recomendadas. Como deseja proceder?",
        choices=[
            "🚀 Executar Todas as Recomendadas Automaticamente",
            "☑️  Escolher Individualmente no Checklist",
            "❌ Cancelar"
        ]
    ).ask()

    if not acao or acao == "❌ Cancelar":
        return []

    plugins_selecionados = []
    if acao == "🚀 Executar Todas as Recomendadas Automaticamente":
        plugins_selecionados = plugins_smart
    else:
        opcoes_ferramentas = [
            questionary.Choice(f"{p['name']} - {p.get('description', '')}", value=p, checked=True)
            for p in plugins_smart
        ]
        plugins_selecionados = questionary.checkbox(
            f"Marque as ferramentas recomendadas para '{tipo}':",
            choices=opcoes_ferramentas
        ).ask()

        if not plugins_selecionados:
            return []

    inputs = {"alvo": alvo}
    console.print(f"[bold yellow]⚡ Rodando {len(plugins_selecionados)} plugins em paralelo...[/bold yellow]")
    with console.status("[bold green]Aguardando containers Docker para processamento...[/bold green]"):
        resultados = run_plugins_paralelo(plugins_selecionados, inputs)

    exibir_resultados(resultados)

    # Persist results if case is active
    if case_id:
        _persistir_resultados(case_id, alvo, resultados, scan_type="direct")

    return resultados


def modo_manual(plugins: list, case_id: int = None):
    """Manual mode — select category and tools individually."""
    categories = {}
    for p in plugins:
        cat = p.get("category", "Outros")
        categories.setdefault(cat, []).append(p)

    cat_escolha = questionary.select(
        "Qual categoria deseja explorar?",
        choices=list(categories.keys()) + ["⬅️  Voltar"]
    ).ask()

    if cat_escolha == "⬅️  Voltar" or not cat_escolha:
        return "", []

    cat_plugins = categories[cat_escolha]

    acao_rapida = questionary.select(
        f"Categoria Selecionada: {cat_escolha} ({len(cat_plugins)} ferramentas)\nComo deseja prosseguir?",
        choices=[
            questionary.Choice("🚀 Executar Todas as Ferramentas (Varredura Completa)", value="all"),
            questionary.Choice("🎯 Escolher Ferramentas Individualmente (Modo Cirúrgico)", value="select"),
            questionary.Choice("⬅️  Voltar", value="back")
        ],
        style=questionary.Style([("pointer", "fg:yellow bold")])
    ).ask()

    if acao_rapida == "back" or not acao_rapida:
        return "", []

    plugins_selecionados = []
    if acao_rapida == "all":
        plugins_selecionados = cat_plugins
    else:
        opcoes_ferramentas = [
            questionary.Choice(f"{p['name']} - {p.get('description', '')}", value=p, checked=True)
            for p in cat_plugins
        ]
        plugins_selecionados = questionary.checkbox(
            "Escolha as ferramentas cirurgicamente:",
            choices=opcoes_ferramentas
        ).ask()

    if not plugins_selecionados:
        return "", []

    inputs_req = {}
    for plugin in plugins_selecionados:
        for campo in plugin.get("inputs", []):
            inputs_req[campo["id"]] = campo

    dados = {}
    alvo = ""
    for id_campo, campo in inputs_req.items():
        resp = questionary.text(campo.get("prompt", f"Alvo para {id_campo}:")).ask()
        if not resp:
            break
        dados[id_campo] = resp
        if not alvo:
            alvo = resp

    if len(dados) != len(inputs_req):
        console.print("[yellow]Investigação cancelada por falta de inputs.[/yellow]")
        return "", []

    execucao_modo = questionary.select(
        "Como deseja executar estas ferramentas?",
        choices=[
            questionary.Choice("⚡ Em Paralelo (Mais rápido)", value="parallel"),
            questionary.Choice("📋 Sequencial (Uma por vez)", value="sequential")
        ]
    ).ask()

    resultados = []
    if execucao_modo == "parallel":
        console.print(f"[bold yellow]⚡ Disparando {len(plugins_selecionados)} plugins em paralelo...[/bold yellow]")
        with console.status("[bold green]Aguardando Docker...[/bold green]"):
            resultados = run_plugins_paralelo(plugins_selecionados, dados)
        exibir_resultados(resultados)
    elif execucao_modo == "sequential":
        for plugin in plugins_selecionados:
            console.print(f"[bold yellow]>> {plugin['name']}...[/bold yellow]")
            with console.status(f"[green]{plugin['name']}...[/green]"):
                res = run_plugin(plugin, dados)
            resultados.append({"name": plugin["name"], "output": res})
        exibir_resultados(resultados)

    # Persist results if case is active
    if case_id and alvo:
        _persistir_resultados(case_id, alvo, resultados, scan_type="manual")

    return alvo, resultados


def _persistir_resultados(case_id: int, alvo: str, resultados: list[dict], scan_type: str = "direct"):
    """Persists scan results to the database — entities, raw results, and notifications."""
    try:
        scan_id = create_scan(case_id, alvo, scan_type=scan_type, plugin_count=len(resultados))

        all_entities = []
        for r in resultados:
            # Save raw result
            save_raw_result(
                scan_id=scan_id,
                plugin_name=r.get("name", "Unknown"),
                target=alvo,
                output=r.get("output", ""),
                layer=r.get("camada", 1)
            )

            # Extract and save entities
            entities = extrair_entidades(
                r.get("output", ""),
                source_tool=r.get("name", ""),
                source_target=alvo
            )
            all_entities.extend(entities)

        if all_entities:
            save_entities(case_id, scan_id, all_entities)

        finish_scan(scan_id, status="completed")

        # Send notification
        case = get_case(case_id)
        insights = extrair_insights(resultados)
        notificar_scan_completo(
            alvo=alvo,
            total_plugins=len(resultados),
            total_entidades=len(all_entities),
            case_name=case.get("name", "") if case else "",
            correlacoes=len(insights.get("correlacoes", []))
        )

        log.info(f"Resultados persistidos: {len(resultados)} plugins, {len(all_entities)} entidades")

    except Exception as e:
        log.error(f"Falha ao persistir resultados: {e}")


def modo_interativo(plugins: list):
    """Main interactive loop with case management."""
    dep_status = check_dependencies()

    # Case selection at startup
    case_id = selecionar_ou_criar_case()

    while True:
        print_banner(len(plugins))

        escolha = questionary.select(
            "Selecione o seu objetivo operacional:",
            choices=[
                questionary.Choice("🎯 Varredura Direta (Rápida e Inteligente)", value="direto"),
                questionary.Choice("🧩 Modo Manual (Arsenal por Categoria)", value="manual"),
                questionary.Choice("🕵️ Investigação em Camadas (Workflow Agente)", value="workflow"),
                questionary.Separator(),
                questionary.Choice("📂 Gerenciar Cases", value="cases"),
                questionary.Choice("🔧 Health Check (Dependências)", value="saude"),
                questionary.Choice("📚 Manual e Tutorial", value="tutorial"),
                questionary.Choice("❌ Encerrar Operação", value="sair")
            ],
            style=questionary.Style([
                ('qmark', 'fg:#FF00FF bold'),
                ('question', 'bold'),
                ('answer', 'fg:#00FFFF bold'),
                ('pointer', 'fg:#00FFFF bold'),
                ('highlighted', 'fg:#00FFFF bold'),
                ('selected', 'fg:#cc5454'),
                ('separator', 'fg:#6C6C6C'),
                ('instruction', 'fg:#808080'),
            ])
        ).ask()

        if escolha in ["sair", None]:
            sys.exit(0)

        if escolha == "saude":
            dep_status = check_dependencies()
            from rich.table import Table
            from rich.panel import Panel
            t = Table(show_header=True, header_style="bold cyan")
            t.add_column("Dependência", width=15)
            t.add_column("Status")
            t.add_column("Detalhe", style="dim")
            for dep, info in dep_status.items():
                status_str = "[green]✅ OK[/green]" if info["ok"] else "[red]❌ FALHA[/red]"
                t.add_row(dep, status_str, info.get("msg", ""))
            console.print(Panel(t, title="🔧 Health Check", border_style="cyan"))
            input("\nPressione ENTER para voltar...")
            continue

        if escolha == "tutorial":
            exibir_tutorial()
            input("\nPressione ENTER para voltar...")
            continue

        if escolha == "cases":
            menu_gerenciar_cases()
            case_id = selecionar_ou_criar_case()
            continue

        resultados = []
        alvo = ""

        if escolha in ["direto", "workflow"]:
            alvo = questionary.text("Alvo (email, telefone, username, URL, cripto, arquivo...):").ask()
            if not alvo:
                continue

            if escolha == "workflow":
                resultados = modo_workflow(alvo, plugins, case_id=case_id)
            else:
                resultados = modo_direto(alvo, plugins, case_id=case_id)

        elif escolha == "manual":
            alvo, resultados = modo_manual(plugins, case_id=case_id)

        if alvo and resultados:
            processar_exportacoes(alvo, resultados)

        if not questionary.confirm("Finalizar sessão atual?").ask():
            continue
        else:
            break


def main():
    parser = argparse.ArgumentParser(description="Colombo Scanner - OSINT Forense via Docker (v3.0 Hardened)")
    parser.add_argument("--alvo", help="Alvo da investigação (direto, sem interface)")
    parser.add_argument("--cat", help="Categoria específica (opcional no modo silencioso)")
    parser.add_argument("--seq", action="store_true", help="Modo sequencial (sem paralelismo)")
    parser.add_argument("--proxy", help="Proxy URL (ex: socks5://127.0.0.1:9050)")
    parser.add_argument("--api", action="store_true", help="Iniciar API REST (FastAPI)")
    args = parser.parse_args()

    # Set proxy in environment if provided
    if args.proxy:
        import os
        os.environ["HTTP_PROXY"] = args.proxy
        os.environ["HTTPS_PROXY"] = args.proxy
        os.environ["COLOMBO_PROXY"] = args.proxy
        log.info(f"Proxy configurado: {args.proxy}")

    if args.api:
        try:
            from api.server import start_api
            start_api()
        except ImportError:
            console.print("[red]FastAPI não instalado. Execute: pip install fastapi uvicorn[/red]")
            sys.exit(1)
        return

    plugins = load_plugins()

    if args.alvo:
        modo_silencioso(args.alvo, categoria=args.cat, paralelo=not args.seq)
    else:
        modo_interativo(plugins)


if __name__ == "__main__":
    main()
