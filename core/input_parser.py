"""
Colombo Scanner — Smart Input Parser
Auto-detects and normalizes any user input format (phones, emails, names, IPs, etc.)
regardless of how the user typed it.
"""
import re
from dataclasses import dataclass, field
from typing import Optional

# ── Ícones por tipo (para exibição) ──────────────────────────────────────────
ICONES_TIPO = {
    "telefone": "📱",
    "email":    "📧",
    "ip":       "🌐",
    "url":      "🔗",
    "dominio":  "🌍",
    "cnpj":     "🏢",
    "cpf":      "🆔",
    "placa":    "🚗",
    "mac":      "💻",
    "cripto":   "💰",
    "github":   "🔒",
    "voo":      "✈️",
    "username": "👤",
    "nome":     "👤",
    "imagem":   "🖼️",
    "arquivo":  "📄",
    "video":    "🎥",
    "audio":    "🎵",
}

PREFIXOS_CRIPTO = ["1", "3", "bc1", "0x", "ltc1", "D", "T"]
EXTENSOES_MIDIA = {
    "video":  [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"],
    "audio":  [".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a"],
    "imagem": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"],
    "arquivo": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt"],
}


@dataclass
class ParsedInput:
    """Represents a single parsed and normalized input."""
    valor_original: str
    valor_normalizado: str
    tipo: str

    @property
    def icone(self) -> str:
        return ICONES_TIPO.get(self.tipo, "🔍")

    def __str__(self):
        return f"{self.icone} {self.tipo.capitalize()}: {self.valor_normalizado}"


# ── Normalização ─────────────────────────────────────────────────────────────

def normalizar_telefone(raw: str) -> str:
    """Remove tudo que não é dígito de um telefone.
    >>> normalizar_telefone("+55 35 999 343 863")
    '5535999343863'
    """
    return re.sub(r"[^\d]", "", raw)


def normalizar_email(raw: str) -> str:
    return raw.strip().lower()


def normalizar_cpf(raw: str) -> str:
    """Remove pontos e hífens de CPF."""
    return re.sub(r"[.\-]", "", raw.strip())


def normalizar_cnpj(raw: str) -> str:
    """Remove pontos, barras e hífens de CNPJ."""
    return re.sub(r"[.\-/]", "", raw.strip())


def normalizar_nome(raw: str) -> str:
    """Title case e trim de espaços extras."""
    return " ".join(raw.split()).strip().title()


# ── Regex patterns ───────────────────────────────────────────────────────────

# Telefone: aceita +, espaços, hífens, parênteses em volta de 8-15 dígitos
_RE_TELEFONE = re.compile(
    r"""
    (?:^|(?<=[\s,;|]))            # deve iniciar no começo ou após delimitador
    (\+?\s*\(?\d{1,4}\)?)         # código de país opcional (ex: +55, (55))
    [\s\-]?                       # separador opcional
    (\(?\d{1,5}\)?)               # DDD/área (ex: 35, (35))
    [\s\-]?
    (\d[\d\s\-]{5,10}\d)          # número em si (6-12 dígitos com espaços/hífens)
    (?=$|[\s,;|])                 # termina no fim ou antes de delimitador
    """,
    re.VERBOSE,
)

_RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.IGNORECASE)
_RE_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_RE_URL = re.compile(r"https?://\S+", re.IGNORECASE)
_RE_DOMINIO = re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}\b", re.IGNORECASE)
_RE_CNPJ = re.compile(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}")
_RE_CPF = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")
_RE_PLACA = re.compile(r"\b[A-Z]{3}-?\d[A-Z\d]\d{2}\b", re.IGNORECASE)
_RE_MAC = re.compile(r"\b(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\b")
_RE_VOO = re.compile(r"\b[A-Z]{2,3}\d{1,4}\b", re.IGNORECASE)


# ── Detecção de tipo para um token limpo ─────────────────────────────────────

def _detectar_tipo_token(token: str) -> tuple[str, str]:
    """Detecta o tipo de um token já isolado. Retorna (tipo, valor_normalizado)."""
    t = token.strip()
    if not t:
        return ("", "")

    lower = t.lower()

    # Email
    if _RE_EMAIL.fullmatch(t):
        return ("email", normalizar_email(t))

    # URL (antes de domínio para não conflitar)
    if _RE_URL.match(t):
        if "github.com" in lower:
            return ("github", t)
        return ("url", t)

    # IP
    if _RE_IP.fullmatch(t):
        return ("ip", t)

    # CNPJ (antes de CPF para não conflitar)
    if _RE_CNPJ.fullmatch(t):
        return ("cnpj", normalizar_cnpj(t))

    # Telefone puro (somente dígitos, 7-15) — ANTES de CPF para evitar falso positivo
    digits_only = re.sub(r"[^\d]", "", t)
    if len(digits_only) >= 7 and len(digits_only) <= 15 and re.match(r"^[\d\s\-\+\(\)]+$", t):
        return ("telefone", normalizar_telefone(t))

    # CPF — só se tiver formatação (pontos/hífens), senão confunde com telefone
    if re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", t):
        return ("cpf", normalizar_cpf(t))

    # Placa de veículo
    if _RE_PLACA.fullmatch(t):
        return ("placa", t.upper().replace("-", ""))

    # MAC address
    if _RE_MAC.fullmatch(t):
        return ("mac", t.lower())

    # Arquivo/mídia (caminhos e extensões)
    for tipo_midia, exts in EXTENSOES_MIDIA.items():
        if any(lower.endswith(ext) for ext in exts):
            return (tipo_midia, t)
    if t.startswith("/") or t.startswith("./"):
        return ("arquivo", t)

    # Domínio
    if _RE_DOMINIO.fullmatch(t) and "." in t and " " not in t:
        if "github.com" in lower:
            return ("github", t)
        return ("dominio", t)

    # Crypto wallet (começa com prefixo específico e >25 chars)
    if any(t.startswith(p) for p in PREFIXOS_CRIPTO) and len(t) > 25:
        return ("cripto", t)

    # Username vs Nome
    if " " in t.strip() and len(t.strip()) > 2:
        return ("nome", normalizar_nome(t))

    # Voo (ex: AD4512) — só se for curto
    if _RE_VOO.fullmatch(t) and len(t) <= 7:
        return ("voo", t.upper())

    return ("username", t.strip())


# ── Separação inteligente do input ───────────────────────────────────────────

def _tokenizar_input(raw: str) -> list[str]:
    """Separa o input bruto em tokens inteligentes.

    Estratégia:
    1. Primeiro extrai padrões especiais (emails, URLs, IPs, telefones com espaços)
    2. Depois separa o resto por delimitadores comuns (vírgula, ponto-e-vírgula, pipe)
    3. Agrupa palavras adjacentes que parecem ser um nome composto
    """
    tokens = []
    remaining = raw.strip()

    # 1) Extrair emails (antes de tudo, para não quebrar por espaços)
    for match in _RE_EMAIL.finditer(remaining):
        tokens.append(match.group())
    remaining = _RE_EMAIL.sub(" §EXTRACTED§ ", remaining)

    # 2) Extrair URLs
    for match in _RE_URL.finditer(remaining):
        tokens.append(match.group())
    remaining = _RE_URL.sub(" §EXTRACTED§ ", remaining)

    # 3) Extrair IPs
    for match in _RE_IP.finditer(remaining):
        tokens.append(match.group())
    remaining = _RE_IP.sub(" §EXTRACTED§ ", remaining)

    # 4) Extrair CNPJs
    for match in _RE_CNPJ.finditer(remaining):
        tokens.append(match.group())
    remaining = _RE_CNPJ.sub(" §EXTRACTED§ ", remaining)

    # 5) Extrair CPFs
    for match in _RE_CPF.finditer(remaining):
        tokens.append(match.group())
    remaining = _RE_CPF.sub(" §EXTRACTED§ ", remaining)

    # 6) Extrair MACs
    for match in _RE_MAC.finditer(remaining):
        tokens.append(match.group())
    remaining = _RE_MAC.sub(" §EXTRACTED§ ", remaining)

    # 7) Extrair telefones com espaços (o mais complexo)
    # Padrão: sequências de dígitos e espaços/hífens que somam 8-15 dígitos
    telefone_pattern = re.compile(
        r"(?:^|(?<=[\s,;|]))"
        r"(\+?\d[\d\s\-\(\)]{6,18}\d)"
        r"(?=$|[\s,;|])"
    )
    for match in telefone_pattern.finditer(remaining):
        candidate = match.group(1).strip()
        digits = re.sub(r"[^\d]", "", candidate)
        if 7 <= len(digits) <= 15:
            tokens.append(candidate)
            remaining = remaining.replace(match.group(), " §EXTRACTED§ ", 1)

    # Limpar marcadores e separar o restante
    remaining = remaining.replace("§EXTRACTED§", "")

    # Separar por delimitadores comuns
    parts = re.split(r"[,;|\n]+", remaining)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Verificar se é uma sequência de palavras (possível nome)
        words = part.split()
        if len(words) == 0:
            continue

        # Se todas as "palavras" são alfabéticas e curtas, é um nome composto
        all_alpha = all(re.match(r"^[a-záàâãéèêíïóôõúüçñ\'\-]+$", w, re.IGNORECASE) for w in words)

        if all_alpha and len(words) >= 2:
            # É um nome composto (ex: "João Silva")
            tokens.append(part)
        elif all_alpha and len(words) == 1:
            tokens.append(words[0])
        else:
            # Pode ter dados misturados, adiciona cada palavra
            for w in words:
                w = w.strip()
                if w:
                    tokens.append(w)

    return [t for t in tokens if t.strip()]


# ── Função principal ─────────────────────────────────────────────────────────

def parse_input_livre(raw_text: str) -> list[ParsedInput]:
    """Parse inteligente de qualquer texto com múltiplos alvos em qualquer formato.

    Aceita entradas como:
      - "5535999453863 +55 35 999343863 35 99945 3863"
      - "joao@gmail.com, João Silva, 11999998888"
      - "192.168.1.1 example.com user@email.com"

    Retorna lista de ParsedInput com tipo detectado e valor normalizado.
    """
    if not raw_text or not raw_text.strip():
        return []

    tokens = _tokenizar_input(raw_text)

    # Remove duplicatas mantendo ordem
    seen = set()
    unique_tokens = []
    for t in tokens:
        key = re.sub(r"[^\w]", "", t.lower())
        if key not in seen:
            seen.add(key)
            unique_tokens.append(t)

    results = []
    for token in unique_tokens:
        tipo, normalizado = _detectar_tipo_token(token)
        if tipo and normalizado:
            results.append(ParsedInput(
                valor_original=token,
                valor_normalizado=normalizado,
                tipo=tipo,
            ))

    return results


def adaptar_para_plugin(parsed: ParsedInput, plugin: dict) -> str:
    """Adapta o valor normalizado para o formato que o plugin espera.

    Exemplos:
    - PhoneInfoga espera telefone com '+' na frente
    - Outros plugins podem esperar o valor cru
    """
    valor = parsed.valor_normalizado
    plugin_name = plugin.get("name", "").lower()
    category = plugin.get("category", "").lower()

    if parsed.tipo == "telefone":
        # Plugins de telefone geralmente esperam formato internacional com +
        if "telefone" in category or "phone" in plugin_name:
            if not valor.startswith("+"):
                # Se tem código de país (>= 10 dígitos), adiciona +
                if len(valor) >= 10:
                    valor = f"+{valor}"
    elif parsed.tipo == "email":
        valor = parsed.valor_normalizado  # Já está limpo
    elif parsed.tipo == "nome":
        # Para buscas que aceitam nome, usar como está
        valor = parsed.valor_normalizado

    return valor


def formatar_resumo_alvos(parsed_list: list[ParsedInput]) -> str:
    """Formata um resumo visual bonito dos alvos detectados para confirmação."""
    if not parsed_list:
        return "  ⚠️  Nenhum alvo detectado."

    linhas = [""]
    for i, p in enumerate(parsed_list, 1):
        linhas.append(f"  {i}. {p.icone} {p.tipo.capitalize()}: [cyan]{p.valor_normalizado}[/cyan]")

    return "\n".join(linhas)
