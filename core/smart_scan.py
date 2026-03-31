import os
from core.input_parser import detectar_tipo

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

def categorias_recomendadas(alvo: str) -> list[str]:
    """retorna categorias ordenadas do mais ao menos relevante pro alvo"""
    tipo = detectar_tipo(alvo)
    return MAPA_TIPOS.get(tipo, ["👤 Identidades e Usernames"])

def filtrar_plugins_smart(plugins: list[dict], alvo: str) -> list[dict]:
    """filtra os plugins pelas categorias certas pro tipo do alvo"""
    cats = categorias_recomendadas(alvo)
    return [p for p in plugins if p.get("category") in cats]
