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

def modo_interativo():
    """loop principal da interface interativa com Dashboard de Modos"""
    while True:
        print_banner()

        plugins = load_plugins()
        if not plugins:
            console.print("[red]nenhum yaml encontrado em plugins/.[/red]")
            return
        modos = [
            questionary.Choice("🧠 Investigação Inteligente (Auto-Deteção)", value="smart"),
            questionary.Choice("⚡ Varredura Paralela (Massiva/Rápida)", value="parallel"),
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
        if modo in ["smart", "parallel"]:
            alvo = questionary.text("Alvo (email, telefone, username, URL, cripto, arquivo...):").ask()
            if not alvo:
                continue

            tipo = detectar_tipo(alvo)
            cats = categorias_recomendadas(alvo)
            console.print(Panel(f"Target: [bold]{alvo}[/bold]\nTipo detectado: [bold yellow]{tipo}[/bold yellow]\nCategorias: [cyan]{', '.join(cats)}[/cyan]", title="Análise Preliminar", border_style="blue"))

            plugins_smart = filtrar_plugins_smart(plugins, alvo)
            if not plugins_smart:
                console.print("[yellow]nenhum plugin encontrado pra esse tipo.[/yellow]")
                continue
            opcoes_ferramentas = [
                questionary.Choice(f"{p['name']} - {p.get('description', '')}", value=p, checked=True)
                for p in plugins_smart
            ]
            
            plugins_selecionados = questionary.checkbox(
                f"Ferramentas automáticas para '{tipo}':",
                choices=opcoes_ferramentas
            ).ask()

            if not plugins_selecionados:
                continue

            inputs = {"alvo": alvo}

            if modo == "parallel":
                console.print(f"[bold yellow]⚡ Rodando {len(plugins_selecionados)} plugins em paralelo...[/bold yellow]")
                with console.status("[bold green]aguardando os containers docker..."):
                    resultados = run_plugins_paralelo(plugins_selecionados, inputs)
            else:
                for plugin in plugins_selecionados:
                    console.print(f"[bold yellow]>> {plugin['name']}...[/bold yellow]")
                    with console.status(f"[green]{plugin['name']}..."):
                        res = run_plugin(plugin, inputs)
                    resultados.append({"name": plugin["name"], "output": res})

            exibir_resultados(resultados)

        elif modo == "manual":
            categories = {}
            for p in plugins:
                cat = p.get("category", "Outros")
                categories.setdefault(cat, []).append(p)

            cat_escolha = questionary.select(
                "Qual categoria deseja explorar?",
                choices=list(categories.keys()) + ["⬅️  Voltar"]
            ).ask()

            if cat_escolha == "⬅️  Voltar":
                continue

            cat_plugins = categories[cat_escolha]
            opcoes_ferramentas = [
                questionary.Choice(f"{p['name']} - {p.get('description', '')}", value=p, checked=True)
                for p in cat_plugins
            ]

            plugins_selecionados = questionary.checkbox(
                f"Escolha as ferramentas que deseja executar da categoria {cat_escolha}:",
                choices=opcoes_ferramentas
            ).ask()

            if not plugins_selecionados:
                continue
            inputs_req = {}
            for plugin in plugins_selecionados:
                for campo in plugin.get("inputs", []):
                    inputs_req[campo["id"]] = campo

            dados = {}
            for id_campo, campo in inputs_req.items():
                resp = questionary.text(campo.get("prompt", f"Alvo para {id_campo}:")).ask()
                if not resp:
                    break
                dados[id_campo] = resp
                if not alvo:
                    alvo = resp

            if len(dados) != len(inputs_req):
                console.print("[yellow]Investigação cancelada por falta de inputs.[/yellow]")
                continue

            execucao_modo = questionary.select(
                "Como deseja executar estas ferramentas?",
                choices=[
                    questionary.Choice("⚡ Em Paralelo (Mais rápido)", value="parallel"),
                    questionary.Choice("📋 Sequencial (Uma por vez)", value="sequential")
                ]
            ).ask()

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
        if resultados:
            opcoes_export = questionary.checkbox(
                "O que quer exportar?",
                choices=[
                    questionary.Choice("📄 Relatório PDF", checked=True),
                    questionary.Choice("🔗 Grafo de Links (HTML interativo)", checked=True)
                ]
            ).ask()


            if not opcoes_export:
                continue

            if "📄 Relatório PDF" in opcoes_export:
                caminho = gerar_relatorio(alvo, resultados)
                console.print(f"\n[bold green]✅ PDF: {caminho}[/bold green]")

            if "🔗 Grafo de Links (HTML interativo)" in opcoes_export:
                caminho_grafo = gerar_grafo(alvo, resultados)
                console.print(f"[bold green]✅ Grafo: {caminho_grafo}[/bold green]\n")

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
