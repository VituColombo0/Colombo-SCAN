import questionary
import argparse
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from core.plugin_manager import load_plugins
from core.runner import run_plugins_paralelo, run_plugin
from core.smart_scan import filtrar_plugins_smart, detectar_tipo, categorias_recomendadas
from core.report import gerar_relatorio
from core.graph import gerar_grafo
from core.health_check import check_dependencies
from core.workflow import executar_workflow_recursivo
from core.intelligence import extrair_insights, exibir_dashboard_inteligencia

console = Console()
check_dependencies()

def print_banner(plugin_count=0):
    print("\033c", end="")
    from rich.columns import Columns
    import platform
    
    # Dashboard Info
    stats = Table.grid(padding=(0, 1))
    stats.add_column(style="cyan", justify="right")
    stats.add_column(style="white")
    stats.add_row("System:", f"{platform.system()} {platform.release()}")
    stats.add_row("Python:", sys.version.split()[0])
    stats.add_row("Plugins:", f"[bold green]{plugin_count}[/bold green] Ativos")
    stats.add_row("Docker:", "[bold sky_blue1]Connected[/bold sky_blue1]")

    # Heartbeat effect simulation
    import random
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
        title="[bold white]V2.5 ELITE EDITION[/bold white]"
    )
    console.print(header_content)

def exibir_tutorial():
    from rich.columns import Columns
    
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
        "O sistema agora correlaciona resultados automaticamente. Se o mesmo email aparecer em "
        "ferramentas diferentes, ele será destaque no seu Painel de Insights."
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

def formatar_saida_terminal(texto: str) -> str:
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
            f"\n\n... ✂️ [Log imenso ocultado visualmente ({len(novas_linhas)} linhas totais). Verifique o Relatório Markdown/CSV para o dado completo] ✂️ ...\n\n" +
            "\n".join(novas_linhas[-5:])
        )
        return truncado

    return "\n".join(novas_linhas)

def exibir_resultados(resultados: list[dict]):
    """imprime os resultados formatados no terminal"""
    # NOVO: Dashboard de Inteligência Correlacionada
    insights = extrair_insights(resultados)
    exibir_dashboard_inteligencia(insights)

    for r in resultados:
        saida = r.get("output", "")
        if not saida:
            saida = "[dim italic]Nenhum dado retornado ou erro no plugin.[/dim italic]"
            
        painel = Panel(
            formatar_saida_terminal(str(saida)),
            title=f"[white]🔍 Resultado: [bold cyan]{r['name']}[/bold cyan]",
            border_style="blue",
            subtitle="[dim]Colombo Reporting Engine[/dim]"
        )
        console.print(painel)
        console.print()

def modo_silencioso(alvo: str, categoria: str = None, paralelo: bool = True):
    """
    modo sem interface: colombo --alvo email@x.com --cat '📧 Análise de Emails'
    util pra rodar via scripts e automacoes externas
    """
    plugins = load_plugins()

    if categoria:
        plugins_rodar = [p for p in plugins if p.get("category") == categoria]
    else:
        plugins_rodar = filtrar_plugins_smart(plugins, alvo)

    if not plugins_rodar:
        console.print(f"[red]nenhum plugin encontrado para o alvo: {alvo}[/red]")
        sys.exit(1)

    tipo = detectar_tipo(alvo)
    console.print(f"[cyan]alvo: {alvo} | tipo: {tipo} | plugins: {len(plugins_rodar)}[/cyan]\n")

    inputs = {"alvo": alvo}

    if paralelo:
        resultados = run_plugins_paralelo(plugins_rodar, inputs)
    else:
        resultados = [{"name": p["name"], "output": run_plugin(p, inputs)} for p in plugins_rodar]

    exibir_resultados(resultados)

    caminho = gerar_relatorio(alvo, resultados)
    console.print(f"\n[bold green]✅ relatorio: {caminho}[/bold green]")
    return resultados

def processar_exportacoes(alvo, resultados):
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

def modo_workflow(alvo: str, plugins: list):
    console.print(Panel(
        "[italic]O Workflow pegará a saída do seu alvo inicial e vai minerar novas informações.\n"
        "O número de 'Camadas' define o quão fundo na toca do coelho o scanner deve ir.[/italic]",
        border_style="magenta", title="🕵️ Modo Operador de Inteligência"
    ))
    
    # NOVO: Filtro de categorias para o Workflow
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
    return resultados

def modo_direto(alvo: str, plugins: list):
    tipo = detectar_tipo(alvo)
    cats = categorias_recomendadas(alvo)
    console.print(Panel(f"Target: [bold]{alvo}[/bold]\nTipo detectado: [bold yellow]{tipo}[/bold yellow]\nCategorias: [cyan]{', '.join(cats)}[/cyan]", title="Análise Preliminar", border_style="blue"))

    plugins_smart = filtrar_plugins_smart(plugins, alvo)
    if not plugins_smart:
        console.print("[yellow]nenhum plugin encontrado pra esse tipo.[/yellow]")
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
    with console.status("[bold green]aguardando os containers docker para processamento...[/bold green]"):
        resultados = run_plugins_paralelo(plugins_selecionados, inputs)

    exibir_resultados(resultados)
    return resultados

def modo_manual(plugins: list):
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
    
    # NOVAS IMPLEMENTAÇÕES - AÇÃO RÁPIDA (Phase 8)
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
            f"Escolha as ferramentas cirurgicamente:",
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
        with console.status("[bold green]aguardando docker..."):
            resultados = run_plugins_paralelo(plugins_selecionados, dados)
        exibir_resultados(resultados)
    elif execucao_modo == "sequential":
        for plugin in plugins_selecionados:
            console.print(f"[bold yellow]>> {plugin['name']}...[/bold yellow]")
            with console.status(f"[green]{plugin['name']}..."):
                res = run_plugin(plugin, dados)
            resultados.append({"name": plugin["name"], "output": res})
        exibir_resultados(resultados)
        
    return alvo, resultados

def modo_interativo(plugins):
    """loop principal da interface interativa com Dashboard de Modos"""
    while True:
        print_banner(len(plugins))
        
        escolha = questionary.select(
            "Selecione o seu objetivo operacional:",
            choices=[
                questionary.Choice("🎯 Varredura Direta (Rápida e Inteligente)", value="direto"),
                questionary.Choice("🧩 Modo Manual (Arsenal por Categoria)", value="manual"),
                questionary.Choice("🕵️ Investigação em Camadas (Workflow Agente)", value="workflow"),
                questionary.Separator(),
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
                ('text', ''),
                ('disabled', 'fg:#858585 italic')
            ])
        ).ask()

        if escolha in ["sair", None]:
            sys.exit(0)

        if escolha in ["saude"]:
            check_dependencies()
            input("\nPressione ENTER para voltar...")
            continue

        if escolha in ["tutorial"]:
            exibir_tutorial()
            input("\nPressione ENTER para voltar...")
            continue

        resultados = []
        alvo = ""
        
        if escolha in ["direto", "workflow"]:
            alvo = questionary.text("Alvo (email, telefone, username, URL, cripto, arquivo...):").ask()
            if not alvo:
                continue

            if escolha == "workflow":
                from core.workflow import modo_workflow
                resultados = modo_workflow(alvo, plugins)
            else:
                from core.runner import modo_direto
                resultados = modo_direto(alvo, plugins)
                
        elif escolha == "manual":
            from core.runner import modo_manual
            alvo, resultados = modo_manual(plugins)

        # Trata as exportacoes se houve resultado
        if alvo and resultados:
            from core.report import processar_exportacoes
            processar_exportacoes(alvo, resultados)

        if not questionary.confirm("Finalizar sessão atual?").ask():
            continue
        else:
            break

def main():
    parser = argparse.ArgumentParser(description="Colombo Scanner - OSINT Forense via Docker")
    parser.add_argument("--alvo", help="Alvo da investigação (direto, sem interface)")
    parser.add_argument("--cat", help="Categoria específica (opcional no modo silencioso)")
    parser.add_argument("--seq", action="store_true", help="Modo sequencial (sem paralelismo)")
    args = parser.parse_args()

    # IMPORTANTE: Carregar plugins aqui para passar para o modo interativo
    from core.plugin_manager import load_plugins
    plugins = load_plugins()

    if args.alvo:
        modo_silencioso(args.alvo, categoria=args.cat, paralelo=not args.seq)
    else:
        modo_interativo(plugins)

if __name__ == "__main__":
    main()
