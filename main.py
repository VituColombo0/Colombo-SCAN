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

console = Console()
check_dependencies()

def print_banner():
    print("\033c", end="")
    banner = """
   ____   ___  _     ___  __  __ ____   ___  
  / ___| / _ \\| |   / _ \\|  \\/  | __ ) / _ \\ 
 | |    | | | | |  | | | | |\\/| |  _ \\| | | |
 | |___ | |_| | |__| |_| | |  | | |_) | |_| |
  \\____| \\___/|_____\\___/|_|  |_|____/ \\___/ 
    [bold cyan]Scanner Forense OSINT | Colombo v2.0[/bold cyan]
    """
    console.print(Panel.fit(banner, border_style="cyan"))

def exibir_tutorial():
    info = (
        "[bold yellow]Como o Colombo Scanner funciona?[/bold yellow]\n\n"
        " O scanner automatiza dezenas de ferramentas OSINT (Docker). Você possui 2 caminhos principais:\n\n"
        " 🎯 [bold green]Varredura Direta:[/bold green] Você insere um alvo (IP, email, placa) e o Scanner detecta o tipo, "
        "recomenda as ferramentas ideais e executa todas de uma vez em paralelo para aquele alvo específico.\n\n"
        " 🕸️ [bold magenta]Workflow Autônomo (Camadas):[/bold magenta] O modo 'Agente'. Você insere um alvo inicial, e ele faz a "
        "varredura. O sistema então lê os resultados da [bold]Camada 1[/bold], extrai novos IPs, E-mails e Telefones que encontrar no texto, e "
        "automaticamente inicia uma nova investigação profunda para essas novas pistas ([bold]Camada 2[/bold]), criando uma rede de inteligência massiva."
    )
    console.print(Panel(info, title="📚 Guia Rápido", border_style="yellow"))

def exibir_resultados(resultados: list[dict]):
    """imprime os resultados formatados no terminal"""
    for r in resultados:
        saida = r.get("output", "")
        if isinstance(saida, str):
            saida = saida.strip()
        else:
            saida = str(saida)
            
        if not saida:
            saida = "[italic dim]Nenhum dado retornado pela ferramenta.[/italic dim]"
            
        painel = Panel(
            saida,
            title=f"🛠️  [bold green]{r['name']}[/bold green]",
            border_style="green",
            expand=False
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
        "O número de 'Camadas' define o quão fundo na toca do coelho o scanner deve ir.\n"
        "Ex: 2 Camadas = Investiga o alvo, acha um IP, investiga esse IP e para.[/italic]",
        border_style="magenta", title="Sobre as Camadas"
    ))
    verbose = questionary.confirm("Ativar Modo Explicativo (Mostrar pensamento do agente no terminal)?", default=True).ask()
    try:
        camadas = int(questionary.text("Quantas camadas de profundidade investigar? (Mín 1, Máx 5):", default="2").ask())
    except ValueError:
        camadas = 2
    resultados = executar_workflow_recursivo(alvo, plugins, max_camadas=camadas, verbose=verbose)
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
        
    opcoes_ferramentas = [
        questionary.Choice(f"{p['name']} - {p.get('description', '')}", value=p, checked=True)
        for p in plugins_smart
    ]
    
    plugins_selecionados = questionary.checkbox(
        f"Ferramentas recomendadas para '{tipo}':",
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

def modo_interativo():
    """loop principal da interface interativa com Dashboard de Modos"""
    while True:
        print_banner()
        exibir_tutorial()

        plugins = load_plugins()
        if not plugins:
            console.print("[red]nenhum yaml encontrado em plugins/.[/red]")
            return
            
        modos = [
            questionary.Choice("🎯 Varredura Direta (Alvo Único / Paralelo)", value="direct"),
            questionary.Choice("🕸️ Workflow Autônomo (Agente de Camadas Profundas)", value="workflow"),
            questionary.Choice("🔧 Consulta Manual (Por Categoria/Ferramenta)", value="manual"),
            questionary.Choice("📁 Abrir Pasta de Relatórios", value="reports"),
            questionary.Choice("🚪 Sair", value="exit"),
        ]

        modo = questionary.select(
            "Selecione o modo de operação:",
            choices=modos,
            style=questionary.Style([("pointer", "fg:cyan bold")])
        ).ask()

        if modo in ["exit", None]:
            sys.exit(0)

        if modo == "reports":
            path = os.path.abspath('relatorios')
            console.print(f"\n[cyan]📂 Os relatórios estão em: [bold]{path}[/bold][/cyan]")
            input("\nPressione ENTER para voltar...")
            continue

        resultados = []
        alvo = ""
        
        if modo in ["direct", "workflow"]:
            alvo = questionary.text("Alvo (email, telefone, username, URL, cripto, arquivo...):").ask()
            if not alvo:
                continue

            if modo == "workflow":
                resultados = modo_workflow(alvo, plugins)
            else:
                resultados = modo_direto(alvo, plugins)
                
        elif modo == "manual":
            alvo, resultados = modo_manual(plugins)

        # Trata as exportacoes se houve resultado
        if alvo and resultados:
            processar_exportacoes(alvo, resultados)

        if not questionary.confirm("Fazer mais uma investigação?").ask():
            break

def main():
    parser = argparse.ArgumentParser(description="Colombo Scanner - OSINT Forense via Docker")
    parser.add_argument("--alvo", help="Alvo da investigação (direto, sem interface)")
    parser.add_argument("--cat", help="Categoria específica (opcional no modo silencioso)")
    parser.add_argument("--seq", action="store_true", help="Modo sequencial (sem paralelismo)")
    args = parser.parse_args()

    if args.alvo:
        modo_silencioso(args.alvo, categoria=args.cat, paralelo=not args.seq)
    else:
        modo_interativo()

if __name__ == "__main__":
    main()
