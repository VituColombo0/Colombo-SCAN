"""
Colombo Scanner — Intelligence Correlation Engine v2
Extracts typed entities from results, correlates across tools, and generates scoring.
"""
import re
from typing import List, Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from core.entities import Entity, EntityType, Relation, RelationType
from core.logger import get_logger

log = get_logger("intelligence")
console = Console()

# Regex patterns for entity extraction
PATTERNS = {
    EntityType.EMAIL: r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    EntityType.IP: r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b',
    EntityType.DOMAIN: r'(?<!@)\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b',
    EntityType.PHONE: r'(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?9?\d{4}[-.\s]?\d{4}',
    EntityType.URL: r'https?://[^\s"\'<>]+',
    EntityType.USERNAME: r'@([\w._]{3,30})',
    EntityType.HASH: r'\b[a-fA-F0-9]{32,64}\b',
    EntityType.CRYPTO_WALLET: r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}\b|0x[a-fA-F0-9]{40}',
}

# Noise filters
IGNORE_IPS = {"127.0.0.1", "0.0.0.0", "255.255.255.255"}
IGNORE_DOMAINS = {"example.com", "localhost", "github.com", "docker.com", "googleapis.com"}
IGNORE_EMAILS = {"noreply@", "no-reply@", "postmaster@", "mailer-daemon@"}


def extrair_entidades(texto: str, source_tool: str = "", source_target: str = "") -> list[Entity]:
    """
    Extracts typed entities from raw text output.
    Returns a deduplicated list of Entity objects.
    """
    if not isinstance(texto, str) or not texto.strip():
        return []

    entities = []
    seen = set()

    for entity_type, pattern in PATTERNS.items():
        matches = re.findall(pattern, texto, re.IGNORECASE)

        for match in matches:
            value = match.strip().lower()

            # Noise filtering
            if entity_type == EntityType.IP and value in IGNORE_IPS:
                continue
            if entity_type == EntityType.IP and value.startswith(("10.", "192.168.", "172.16.")):
                continue
            if entity_type == EntityType.DOMAIN and value in IGNORE_DOMAINS:
                continue
            if entity_type == EntityType.EMAIL and any(value.startswith(x) for x in IGNORE_EMAILS):
                continue
            if entity_type == EntityType.PHONE:
                digits = re.sub(r'\D', '', value)
                if len(digits) < 10:
                    continue
                value = digits
            if entity_type == EntityType.HASH:
                # Skip if it looks like a common hex string (not a real hash)
                if len(value) not in (32, 40, 64):
                    continue

            key = (entity_type, value)
            if key not in seen:
                seen.add(key)
                entities.append(Entity(
                    type=entity_type,
                    value=value if entity_type != EntityType.USERNAME else match,
                    source_tool=source_tool,
                    source_target=source_target
                ))

    log.debug(f"[{source_tool}] Extraídas {len(entities)} entidades de {len(texto)} chars")
    return entities


def extrair_insights(resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts intelligence insights from scan results.
    Returns structured insights with scoring and correlation data.
    """
    all_entities: list[Entity] = []
    alertas = []
    entity_sources: dict[str, set] = {}  # value -> set of tools

    for res in resultados:
        ferramenta = res.get("name", "Unknown")
        saida = str(res.get("output", ""))
        alvo = res.get("alvo_origem", "")

        # Extract entities
        entities = extrair_entidades(saida, source_tool=ferramenta, source_target=alvo)
        all_entities.extend(entities)

        # Track which tools found each entity
        for e in entities:
            entity_sources.setdefault(e.value, set()).add(ferramenta)

        # Detect identity matches in known tools
        if any(x in ferramenta.lower() for x in ["maigret", "sherlock", "holehe", "blackbird", "socialscan"]):
            if "http" in saida or "found" in saida.lower() or "claimed" in saida.lower():
                alertas.append(f"Identidade detectada via [bold cyan]{ferramenta}[/bold cyan]")

        # Detect messaging platform links
        if "t.me/" in saida:
            alertas.append(f"Link Telegram encontrado por [bold cyan]{ferramenta}[/bold cyan]")
        if "discord.gg/" in saida or "discord.com/invite/" in saida:
            alertas.append(f"Link Discord encontrado por [bold cyan]{ferramenta}[/bold cyan]")

    # Group entities by type
    by_type: dict[EntityType, list[Entity]] = {}
    for e in all_entities:
        by_type.setdefault(e.type, []).append(e)

    # Find correlations (entities found by multiple tools)
    correlacoes = []
    for value, tools in entity_sources.items():
        if len(tools) > 1:
            correlacoes.append({
                "value": value,
                "tools": list(tools),
                "score": len(tools)
            })
    correlacoes.sort(key=lambda x: x["score"], reverse=True)

    # Deduplicate entities by value
    unique_entities = {}
    for e in all_entities:
        if e.value not in unique_entities:
            unique_entities[e.value] = e

    return {
        "entities": list(unique_entities.values()),
        "by_type": {k.value: [e.value for e in v] for k, v in by_type.items()},
        "correlacoes": correlacoes,
        "alertas": alertas,
        "total_raw": len(all_entities),
        "total_unique": len(unique_entities),
    }


def exibir_dashboard_inteligencia(insights: Dict[str, Any]):
    """Displays the enhanced intelligence dashboard with correlations and scoring."""
    entities = insights.get("entities", [])
    correlacoes = insights.get("correlacoes", [])
    alertas = insights.get("alertas", [])
    by_type = insights.get("by_type", {})

    if not entities and not alertas:
        return

    # Main stats table
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column(style="cyan", justify="right")
    stats_table.add_column(style="white")
    stats_table.add_row("Entidades únicas:", str(insights.get("total_unique", 0)))
    stats_table.add_row("Correlações:", f"[bold yellow]{len(correlacoes)}[/bold yellow]")

    console.print(Panel(stats_table, title="[bold]📊 Resumo Rápido[/bold]", border_style="blue"))

    # Entity breakdown table
    if by_type:
        entity_table = Table(
            title="🧠 Inteligência Correlacionada",
            show_header=True,
            header_style="bold magenta",
            expand=True
        )
        entity_table.add_column("Tipo", style="dim", width=20)
        entity_table.add_column("Descobertas", style="white")
        entity_table.add_column("Qtd", style="cyan", width=6, justify="center")

        type_emojis = {
            "email": "📧", "ip": "🌐", "domain": "🔗", "username": "👤",
            "phone": "📱", "url": "🔗", "hash": "#️⃣", "crypto": "₿",
            "social_profile": "📲"
        }

        for tipo, valores in by_type.items():
            emoji = type_emojis.get(tipo, "🔹")
            display_values = ", ".join(valores[:5])
            if len(valores) > 5:
                display_values += f" (+{len(valores) - 5})"
            entity_table.add_row(f"{emoji} {tipo.upper()}", display_values, str(len(valores)))

        console.print(Panel(entity_table, border_style="magenta"))

    # Correlation highlights
    if correlacoes:
        corr_table = Table(
            title="🔥 Correlações (mesmo dado em múltiplas fontes)",
            show_header=True,
            header_style="bold yellow",
            expand=True
        )
        corr_table.add_column("Valor", style="white")
        corr_table.add_column("Score", style="bold yellow", width=8, justify="center")
        corr_table.add_column("Fontes", style="dim")

        for c in correlacoes[:10]:
            corr_table.add_row(
                c["value"][:50],
                f"⭐ {c['score']}",
                ", ".join(c["tools"][:4])
            )

        console.print(Panel(corr_table, border_style="yellow"))

    # Alerts
    if alertas:
        for alerta in alertas[:5]:
            console.print(f"  ⚠️  {alerta}")
        console.print()
