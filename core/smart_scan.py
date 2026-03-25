import re
from core.input_parser import normalizar_telefone

MAPA_TIPOS = {
    "email":    ["📧 Análise de Emails", "👤 Identidades e Usernames", "🔍 Inteligência de Busca"],
    "telefone": ["📱 Inteligência de Telefones"],
    "url":      ["🌐 Redes e IPs", "🔐 Vazamentos Profundos", "📄 Documentos e Arquivos"],
    "ip":       ["🌐 Redes e IPs", "🌍 Geolocalização", "💻 IoT e Dispositivos"],
    "imagem":   ["🖼️ Análise de Imagens", "🔍 Busca Reversa de Imagem", "📄 Documentos e Arquivos"],
    "arquivo":  ["🖼️ Análise de Imagens", "📄 Documentos e Arquivos"],
    "pdf":      ["📄 Documentos e Arquivos"],
    "video":    ["🎙️ Áudio e Vídeo Forense"],
    "audio":    ["🎙️ Áudio e Vídeo Forense"],
    "username": ["👤 Identidades e Usernames", "📧 Análise de Emails", "🔐 Vazamentos Profundos", "🔍 Inteligência de Busca"],
    "nome":     ["👤 Identidades e Usernames", "🔍 Inteligência de Busca"],
    "cpf":      ["👤 Identidades e Usernames", "🔍 Inteligência de Busca"],
    "github":   ["🔒 DevSecOps & Repositories", "🔐 Vazamentos Profundos", "👤 Identidades e Usernames"],
    "cripto":   ["💰 Rastreio de Criptomoedas", "🔐 Vazamentos Profundos"],
    "dominio":  ["🕸️ Attack Surface Mapping", "🌐 Redes e IPs", "🌍 Geolocalização", "💻 IoT e Dispositivos", "🔍 Inteligência de Busca", "🔐 Vazamentos Profundos"],
    "cnpj":     ["🏢 Corporate & CNPJ"],
    "placa":    ["🚗 Veículos e Placas"],
    "mac":      ["💻 IoT e Dispositivos", "🌐 Redes e IPs"],
    "voo":      ["✈️ Rastreador de Voos"]
}

EXTENSOES_VIDEO = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"]
EXTENSOES_AUDIO = [".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a"]
EXTENSOES_IMAGEM = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"]
EXTENSOES_DOC    = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt"]

PREFIXOS_CRIPTO = ["1", "3", "bc1", "0x", "ltc1", "D", "T"]

def detectar_tipo(alvo: str) -> str:
    """heuristica que tenta adivinhar o tipo do alvo com base no formato"""
    a = alvo.strip().lower()

    if re.match(r'^[\w.+-]+@[\w-]+\.[a-z]{2,}$', a):
        return "email"

    # Telefone: normaliza removendo espaços/hífens/parênteses e verifica
    digits = normalizar_telefone(a)
    if re.match(r'^[\+\d\s\-\(\)]{7,20}$', a) and 7 <= len(digits) <= 15:
        return "telefone"

    if re.match(r'^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$', a):
        return "cnpj"
    # CPF
    if re.match(r'^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$', a):
        return "cpf"
    if re.match(r'^[a-z]{3}-?\d[a-z\d]\d{2}$', a):
        return "placa"
    if re.match(r'^([0-9a-f]{2}[:-]){5}([0-9a-f]{2})$', a):
        return "mac"
    if re.match(r'^[a-z]{2,3}\d{1,4}$', a):
        return "voo"

    if "github.com" in a:
        return "github"

    if any(a.endswith(ext) for ext in EXTENSOES_VIDEO):
        return "video"

    if any(a.endswith(ext) for ext in EXTENSOES_AUDIO):
        return "audio"

    if any(a.endswith(ext) for ext in EXTENSOES_IMAGEM):
        return "imagem"
    if any(a.endswith(ext) for ext in EXTENSOES_DOC):
        return "pdf" if a.endswith(".pdf") else "arquivo"

    if re.match(r'^(https?|ftp)://', a):
        return "url"

    if re.match(r'^\d{1,3}(\.\d{1,3}){3}', a):
        return "ip"

    if re.match(r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$', a):
        return "dominio"
    alvo_orig = alvo.strip()
    if any(alvo_orig.startswith(p) for p in PREFIXOS_CRIPTO) and len(alvo_orig) > 25:
        return "cripto"
    if alvo_orig.startswith("/") or alvo_orig.startswith("./"):
        return "arquivo"

    return "username"

def categorias_recomendadas(alvo: str) -> list[str]:
    """retorna categorias ordenadas do mais ao menos relevante pro alvo"""
    tipo = detectar_tipo(alvo)
    return MAPA_TIPOS.get(tipo, ["👤 Identidades e Usernames"])

def filtrar_plugins_smart(plugins: list[dict], alvo: str) -> list[dict]:
    """filtra os plugins pelas categorias certas pro tipo do alvo"""
    cats = categorias_recomendadas(alvo)
    return [p for p in plugins if p.get("category") in cats]
