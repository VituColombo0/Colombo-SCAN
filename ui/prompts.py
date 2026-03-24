"""
Colombo Scanner v4.0 — Prompts & Menus
Interface interativa com os modos clássicos e opção de multi-alvos.
"""
import questionary
import re
from rich.console import Console

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

def escolher_plugins_manual(categorias: dict) -> list:
    """Interface multi-seleção de plugins por categoria."""
    cat_escolha = questionary.select(
        "Qual categoria deseja explorar?",
        choices=list(categorias.keys()) + ["⬅️  Voltar"]
    ).ask()

    if cat_escolha == "⬅️  Voltar" or not cat_escolha:
        return []

    cat_plugins = categorias[cat_escolha]
    opcoes = [
        questionary.Choice(f"{p['name']} - {p.get('description', '')}", value=p, checked=True)
        for p in cat_plugins
    ]
    
    return questionary.checkbox(
        f"Escolha as ferramentas em {cat_escolha}:",
        choices=opcoes
    ).ask()

def perguntar_alvos(prompt_text: str = "Alvo(s) (para vários, separe por vírgula):") -> list[str]:
    raw = questionary.text(prompt_text).ask()
    if not raw:
        return []

    if "," in raw:
        partes = [p.strip() for p in raw.split(",")]
    else:
        partes = [raw.strip()]

    return [p for p in partes if p]

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
    ).ask()
