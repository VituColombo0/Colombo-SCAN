import re
from typing import List, Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

console = Console()

def extrair_insights(resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Definindo explicitamente as coleções para evitar erros de tipo
    emails_set = set()
    links_set = set()
    alertas_list = []
    
    pattern_email = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    for res in resultados:
        ferramenta = res.get("name", "Unknown")
        saida = str(res.get("output", ""))
        
        # 1. Busca por Emails
        emails_encontrados = re.findall(pattern_email, saida)
        for e in emails_encontrados:
            emails_set.add(e)
            
        # 2. Correlação de Identidade (Social Media)
        if any(x in ferramenta.lower() for x in ["maigret", "sherlock", "holehe"]):
            if "http" in saida or "found" in saida.lower():
                alertas_list.append(f"Identidade detectada via [bold cyan]{ferramenta}[/bold cyan]")

        # 3. Menções a Chat Apps
        if "t.me/" in saida:
            links_set.add("Link de Telegram")
        if "discord" in saida.lower():
            links_set.add("Link de Discord")

    return {
        "emails": list(emails_set),
        "links": list(links_set),
        "alertas": alertas_list
    }

def exibir_dashboard_inteligencia(insights: Dict[str, Any]):
    if not any([insights["emails"], insights["links"], insights["alertas"]]):
        return

    table = Table(title="🧠 Resumo de Inteligência Correlacionada", show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Categoria", style="dim", width=20)
    table.add_column("Descobertas / Conexões", style="white")

    emails = insights.get("emails", [])
    if emails:
        table.add_row("📧 Emails Vinculados", ", ".join(emails[:5]))
    
    links = insights.get("links", [])
    if links:
        table.add_row("🔗 Presença Digital", ", ".join(links))

    alertas = insights.get("alertas", [])
    if alertas:
        for alerta in alertas[:3]:
            table.add_row("⚠️ Alerta de Match", alerta)

    console.print("\n")
    console.print(Panel(table, border_style="magenta", subtitle="Colombo Correlation Engine v1.0"))
