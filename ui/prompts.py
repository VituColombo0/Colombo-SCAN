"""
Colombo Scanner v4.1 — Prompts & Menus
Interface interativa com Smart Input Parser, "Executar Todas" e detalhes de ferramentas.
"""
import questionary
import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from core.input_parser import parse_input_livre, formatar_resumo_alvos, ParsedInput

console = Console()

def menu_principal() -> str:
    return questionary.select(
        "Selecione o modo de investigação:",
        choices=[
            {"name": "🎯 Investigação Automática (Inteligente)", "value": "auto"},
            {"name": "🧩 Modo Manual (Escolher Ferramentas)", "value": "manual"},
            {"name": "📂 Gerenciar Cases (Histórico)", "value": "cases"},
            {"name": "💡 Tutorial / Ajuda", "value": "tutorial"},
            {"name": "❌ Sair", "value": "sair"}
        ],
        style=questionary.Style([
            ('qmark', 'fg:cyan bold'),
            ('question', 'bold'),
            ('pointer', 'fg:blue bold'),
            ('selected', 'fg:blue bold'),
        ])
    ).ask()


def _mostrar_detalhes_ferramenta(plugin: dict):
    """Exibe os detalhes e parâmetros de uma ferramenta selecionada."""
    nome = plugin.get("name", "?")
    desc = plugin.get("description", "Sem descrição")
    comando = plugin.get("command", "?")
    imagem = plugin.get("image", "—")
    timeout = plugin.get("timeout", 300)
    tipo = plugin.get("type", "local")
    inputs_cfg = plugin.get("inputs", [])

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="cyan bold", justify="right", width=14)
    table.add_column(style="white")
    table.add_row("Ferramenta:", nome)
    table.add_row("Descrição:", desc)
    table.add_row("Tipo:", f"🐳 Docker ({imagem})" if tipo == "docker" and imagem != "—" else "💻 Local")
    table.add_row("Comando:", f"[bold yellow]{comando}[/bold yellow]")
    table.add_row("Timeout:", f"{timeout}s")

    # Extrair flags/parâmetros do comando
    flags = re.findall(r'(-{1,2}[a-zA-Z][\w\-]*)', comando)
    if flags:
        table.add_row("Parâmetros:", " ".join(f"[green]{f}[/green]" for f in flags))
    else:
        table.add_row("Parâmetros:", "[dim]Nenhum flag explícito[/dim]")

    # Inputs configurados
    inputs_str = ", ".join(f"[cyan]{i.get('id', '?')}[/cyan]" for i in inputs_cfg) if inputs_cfg else "[dim]alvo[/dim]"
    table.add_row("Entradas:", inputs_str)

    console.print(Panel(table, title=f"[bold]📋 {nome}[/bold]", border_style="blue", width=60))


def escolher_plugins_manual(categorias: dict) -> list:
    """Interface multi-seleção de plugins por categoria, com opção 'Executar Todas' e detalhes."""
    opcoes_categoria = ["🔥 Executar TODAS as Ferramentas"] + list(categorias.keys()) + ["⬅️  Voltar"]

    cat_escolha = questionary.select(
        "Qual categoria deseja explorar?",
        choices=opcoes_categoria
    ).ask()

    if cat_escolha == "⬅️  Voltar" or not cat_escolha:
        return []

    # ── "Executar Todas" ─────────────────────────────────────────────
    if cat_escolha == "🔥 Executar TODAS as Ferramentas":
        todos_plugins = []
        for cat_plugins in categorias.values():
            todos_plugins.extend(cat_plugins)

        console.print(f"\n[bold yellow]⚡ {len(todos_plugins)} ferramentas selecionadas de {len(categorias)} categorias.[/bold yellow]")

        confirma = questionary.confirm(
            f"Deseja executar todas as {len(todos_plugins)} ferramentas?", default=True
        ).ask()

        if confirma:
            return todos_plugins
        return []

    # ── Seleção normal por categoria ───────────────────────────────────
    cat_plugins = categorias[cat_escolha]

    # Mostrar detalhes de cada ferramenta da categoria antes de selecionar
    console.print(f"\n[bold cyan]🛠️  Ferramentas em {cat_escolha}:[/bold cyan]\n")
    for p in cat_plugins:
        _mostrar_detalhes_ferramenta(p)
    console.print()

    opcoes = [
        questionary.Choice(f"{p['name']} - {p.get('description', '')}", value=p, checked=True)
        for p in cat_plugins
    ]

    return questionary.checkbox(
        f"Escolha as ferramentas em {cat_escolha}:",
        choices=opcoes
    ).ask() or []


def perguntar_alvos(prompt_text: str = "Alvo(s) (ou caminho para um arquivo .txt com alvos):") -> tuple[list[str], list[ParsedInput]]:
    """Pergunta os alvos e faz parse inteligente. Retorna (lista_alvos, parsed_inputs)."""
    raw = questionary.text(prompt_text).ask()
    if not raw:
        return [], []

    # Se a entrada for um arquivo existente, lê o conteúdo
    import os
    if os.path.isfile(raw.strip()):
        try:
            with open(raw.strip(), 'r', encoding='utf-8') as f:
                content = f.read()
                console.print(f"[dim]Lendo {len(content)} caracteres do arquivo {raw.strip()}...[/dim]")
                raw = content
        except Exception as e:
            console.print(f"[red]Erro ao ler o arquivo {raw.strip()}: {e}[/red]")
            return [], []

    parsed = parse_input_livre(raw)

    if not parsed:
        # Fallback: trata o input inteiro como um único alvo
        console.print("[yellow]⚠️  Não foi possível detectar o tipo. Tratando como alvo único.[/yellow]")
        return [raw.strip()], []

    # Exibir resumo visual para confirmação
    console.print("\n[bold cyan]📋 Alvos detectados:[/bold cyan]")
    console.print(formatar_resumo_alvos(parsed))
    console.print()

    confirma = questionary.confirm("Os alvos estão corretos?", default=True).ask()

    if not confirma:
        # Permite ao usuário re-digitar
        return perguntar_alvos(prompt_text)

    # Retorna tanto a lista de alvos normalizados quanto os ParsedInputs completos
    alvos = [p.valor_normalizado for p in parsed]
    return alvos, parsed


def perguntar_parametros_auto() -> dict:
    """Coleta parâmetros extras para o modo de Investigação Automática."""
    aprofundar = questionary.confirm(
        "Deseja aprofundar a investigação recursivamente (Workflow)?", default=False
    ).ask()

    layers = 1
    if aprofundar:
        layers = questionary.select(
            "Nível de profundidade (Camadas):",
            choices=["2 (Recomendado)", "3 (Demorado)"],
            default="2 (Recomendado)"
        ).ask()
        layers = int(layers[0])

    return {"aprofundar": aprofundar, "layers": layers}


def menu_exportacao(alvo: str) -> list:
    return questionary.checkbox(
        f"Como deseja exportar os resultados?",
        choices=[
            {"name": "📄 PDF (Relatório Profissional)", "value": "pdf", "checked": True},
            {"name": "📊 Grafo de Entidades (HTML)", "value": "grafo", "checked": True},
            {"name": "JSON (Dados Brutos)", "value": "json"},
            {"name": "CSV (Planilha)", "value": "csv"}
        ]
    ).ask() or []
