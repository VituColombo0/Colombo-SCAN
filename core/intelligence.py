"""
Colombo Scanner — Intelligence Correlation Engine v2
Extracts typed entities from results, correlates across tools, and generates scoring.
"""
import re
from typing import List, Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from core.entities import Entity, EntityType, Relation, RelationType, ScanResult
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
    EntityType.USERNAME: r'(?<![\w.-])@([a-zA-Z0-9._-]{3,30})',
    EntityType.HASH: r'\b[a-fA-F0-9]{32,64}\b',
    EntityType.CRYPTO_WALLET: r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}\b|0x[a-fA-F0-9]{40}',
    # Brazilian Specifics
    EntityType.CPF: r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
    EntityType.CNPJ: r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b',
}

# Noise words (don't treat common names/fragments as useful usernames/leads)
NOISE_WORDS = {
    "maria", "vitoria", "jose", "santos", "silva", "oliveira", "souza", "pereira",
    "costa", "carvalho", "alves", "ferreira", "barboza", "gonçalves", "martins",
    "rodrigues", "da silva", "dos santos", "melo", "cardoso", "teixeira",
    "admin", "root", "test", "null", "undefined", "true", "false", "user", "guest",
    "login", "proxy", "server", "client", "default", "none",
    "dos", "da", "de", "do", "das", "pelo", "pela", "index", "home", "search",
    "senha", "password", "whatsapp", "vcard", "charset", "encoding"
}

# Noise filters
IGNORE_IPS = {"127.0.0.1", "0.0.0.0", "255.255.255.255", "8.8.8.8", "8.8.4.4", "1.1.1.1"}
IGNORE_DOMAINS = {"example.com", "localhost", "github.com", "docker.com", "googleapis.com", 
                  "schemas.microsoft.com", "w3.org", "w.org", "purl.org", "schema.org", "google.com", "bing.com"}
IGNORE_EMAILS = {"noreply@", "no-reply@", "postmaster@", "mailer-daemon@", "admin@", "test@", "support@", "contato@"}

# Technical Noise Signatures (Tool failures, empty hits, etc.)
NOISE_SIGNATURES = [
    "no information available", "no address for", "failed to resolve",
    "name does not resolve", "could not resolve hostname", "stat 3a",
    "authentication failed", "unauthorized", "access denied",
    "invalid api key", "hibp-api-key", "wrong ip", "invalid query",
    "scan aborted", "could not run nuclei", "no templates provided",
    "no assets were discovered", "failed to resolve", "fatal: invalid url",
    "sh: 1: shodan: not found", "unable to find image", "pull access denied",
    "did not return any results", "no matches found", "zero results",
    "sem vcard", "sem whats", "unknown error", "required module not found",
    "sh: syntax error", "jq: error", "invalid host"
]

def is_meaningful_result(res: ScanResult) -> bool:
    """
    Determines if a scan result contains useful data or just technical noise.
    """
    saida = str(res.raw_output).lower().strip()
    
    # Empty output is noise
    if not saida:
        return False
        
    # Check for known noise signatures
    if any(sig in saida for sig in NOISE_SIGNATURES):
        return False
        
    # Check if it's just a common banner/art without data
    if len(saida) < 10 and not re.search(r'[a-zA-Z0-9]', saida):
        return False
        
    # Special case: WPScan banner without findings
    if "wpscan team" in saida and "scan aborted" in saida:
        return False

    return True

def strip_ansi(texto: str) -> str:
    """Removes terminal color codes before regex processing."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', texto)

def extrair_entidades(texto: str, source_tool: str = "", source_target: str = "") -> list[Entity]:
    """
    Extracts typed entities from raw text output.
    Returns a deduplicated list of Entity objects.
    """
    if not isinstance(texto, str) or not texto.strip():
        return []

    texto = strip_ansi(texto)
    entities = []
    seen = set()

    for entity_type, pattern in PATTERNS.items():
        matches = re.findall(pattern, texto, re.IGNORECASE)

        for match in matches:
            value = match.strip().lower()

            # Global noise word filter (skip if entity value is just a common word)
            if value in NOISE_WORDS or (len(value) < 3 and entity_type != EntityType.IP):
                continue

            # Type-specific filtering
            if entity_type == EntityType.IP:
                if value in IGNORE_IPS or value.startswith(("10.", "192.168.", "172.16.")):
                    continue
            
            if entity_type == EntityType.DOMAIN:
                if value in IGNORE_DOMAINS or "." not in value or value.endswith((".js", ".css", ".png", ".jpg")):
                    continue
            
            if entity_type == EntityType.EMAIL:
                if any(value.startswith(x) for x in IGNORE_EMAILS) or "@localhost" in value:
                    continue
            
            if entity_type == EntityType.PHONE:
                digits = re.sub(r'\D', '', value)
                if len(digits) < 7 or len(digits) > 15:
                    continue
                # Normalize phone formats roughly. We don't overwrite if it looks international.
                value = f"+{digits}" if not value.startswith('+') and len(digits) >= 10 and not digits.startswith('55') else digits

            
            if entity_type == EntityType.HASH:
                # Skip if it looks like a common hex string (not a real hash)
                if len(value) not in (32, 40, 64):
                    continue

            key = (entity_type, value)
            if key not in seen:
                seen.add(key)
                # Keep original case for usernames if needed (regex groups)
                clean_value = value if entity_type != EntityType.USERNAME else match
                if clean_value.startswith("@"): clean_value = clean_value[1:]
                
                entities.append(Entity(
                    type=entity_type,
                    value=clean_value,
                    source_tool=source_tool,
                    source_target=source_target
                ))

    log.debug(f"[{source_tool}] Extraídas {len(entities)} entidades de {len(texto)} chars")
    return entities


def extrair_insights(resultados: List[ScanResult]) -> Dict[str, Any]:
    """
    Extracts intelligence insights from scan results.
    Returns structured insights with scoring and correlation data.
    """
    all_entities: list[Entity] = []
    alertas = []
    entity_sources: dict[str, set] = {}  # value -> set of tools
    resultados_positivos = []
    resultados_ruido = []

    for res in resultados:
        ferramenta = res.plugin_name
        saida = str(res.raw_output)
        alvo = res.target

        # Check for meaningful data
        relevante = is_meaningful_result(res)
        
        # Extract and merge entities
        entities = extrair_entidades(saida, source_tool=ferramenta, source_target=alvo)
        
        # Merge already structured entities if present
        if res.entities_found:
            for e in res.entities_found:
                if not e.source_tool: e.source_tool = ferramenta
                if not e.source_target: e.source_target = alvo
                entities.append(e)

        all_entities.extend(entities)

        if relevante or entities:
            resultados_positivos.append(res)
        else:
            resultados_ruido.append(res)

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
            # Score de Centralidade e Risco
            e_type = next((e.type for e in all_entities if e.value == value), EntityType.UNKNOWN)
            source_targets = {e.source_target for e in all_entities if e.value == value and e.source_target}
            
            # Matématica Básica: 1 Ponto por ferramenta + 2 pontos por cada origem cruzada diferente
            score = len(tools) + (len(source_targets) * 2) 
            
            correlacoes.append({
                "value": value,
                "type": e_type,
                "tools": list(tools),
                "source_targets": list(source_targets),
                "score": score
            })
    correlacoes.sort(key=lambda x: x["score"], reverse=True)

    # Deduplicate entities by value
    unique_entities = {}
    for e in all_entities:
        if e.value not in unique_entities:
            unique_entities[e.value] = e

    return {
        "entities": list(unique_entities.values()),
        "by_type": {getattr(k, 'value', k): v for k, v in by_type.items()},
        "correlacoes": correlacoes,
        "alertas": alertas,
        "total_raw": len(all_entities),
        "total_unique": len(unique_entities),
        "total_correlations": len(correlacoes),
        "positivos": resultados_positivos,
        "ruido": resultados_ruido
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
    stats_table.add_column(style="bright_blue", justify="right")
    stats_table.add_column(style="white")
    stats_table.add_row("UNIQUE TARGETS:", str(insights.get("total_unique", 0)))
    stats_table.add_row("CROSS-TOOL CORRELATIONS:", f"[bold yellow]{len(correlacoes)}[/bold yellow]")
    stats_table.add_row("HIGH-RISK ALERTS:", f"[bold red]{len(alertas)}[/bold red]")

    console.print(Panel(stats_table, title="[bold white]🛰️ INTELLIGENCE SUMMARY[/bold white]", border_style="bright_black"))

    # Entity breakdown table
    if by_type:
        entity_table = Table(
            title="[bold yellow]🧠 CROSS-CORRELATED INTELLIGENCE[/bold yellow]",
            show_header=True,
            header_style="bold bright_blue",
            expand=True,
            border_style="bright_black"
        )
        entity_table.add_column("CLASSIFICATION", style="dim", width=20)
        entity_table.add_column("DISCOVERED ASSETS", style="white")
        entity_table.add_column("COUNT", style="bright_cyan", width=6, justify="center")

        type_emojis = {
            "email": "📧", "ip": "🌐", "domain": "🔗", "username": "👤",
            "phone": "📱", "url": "🔗", "hash": "#️⃣", "crypto": "₿",
            "social_profile": "📲", "CPF": "🪪", "CNPJ": "🏢", "DATE": "📅"
        }

        for tipo, entities in sorted(by_type.items()):
            emoji = type_emojis.get(tipo, "🔹")
            # Extrair valores únicos das entidades
            unique_vals = list(dict.fromkeys([e.value for e in entities]))
            display_values = ", ".join(unique_vals[:5])
            if len(unique_vals) > 5:
                display_values += f" [dim](+{len(unique_vals) - 5} more)[/dim]"
            entity_table.add_row(f"{emoji} {tipo.upper()}", display_values, str(len(unique_vals)))

        console.print(Panel(entity_table, border_style="bright_blue"))

    # Correlation highlights
    if correlacoes:
        corr_table = Table(
            title="[bold red]🔥 CENTRAL NODES & SIGNAL CORRELATIONS[/bold red]",
            show_header=True,
            header_style="bold yellow",
            expand=True,
            border_style="bright_black"
        )
        corr_table.add_column("CONFIDENCE", style="bold yellow", width=12, justify="center")
        corr_table.add_column("IDENTITY / ASSET", style="white")
        corr_table.add_column("TACTICAL SOURCES", style="dim")
        corr_table.add_column("PIVOTS", style="bright_cyan")

        for c in correlacoes[:10]:
            is_high = c["score"] >= 8
            is_medium = c["score"] >= 4
            
            if is_high:
                score_text = f"🚨 [bold red]CRITICAL ({c['score']})[/bold red]"
                valor_text = f"[bold red]{c['value'][:50]}[/bold red]"
            elif is_medium:
                score_text = f"⚡ [yellow]HIGH ({c['score']})[/yellow]"
                valor_text = f"[bold white]{c['value'][:50]}[/bold white]"
            else:
                score_text = f"⭐ [dim]LOW ({c['score']})[/dim]"
                valor_text = f"[dim]{c['value'][:50]}[/dim]"
            
            corr_table.add_row(
                score_text,
                valor_text,
                ", ".join(c["tools"][:4]),
                f"{len(c['source_targets'])} origins"
            )

        console.print(Panel(corr_table, border_style="yellow"))

    # Alerts
    if alertas:
        for alerta in alertas[:5]:
            console.print(f"  ⚠️  {alerta}")
        console.print()
