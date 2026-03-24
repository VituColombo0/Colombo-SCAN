import re

# Noise words/fragments that should never be treated as valid investigative leads
NOISE_WORDS = {
    "maria", "vitoria", "jose", "santos", "silva", "oliveira", "souza", "pereira",
    "costa", "carvalho", "alves", "ferreira", "barboza", "gonçalves", "martins",
    "admin", "root", "test", "null", "undefined", "true", "false", "user", "guest",
    "senha", "password", "login", "proxy", "server", "client", "default", "none",
    "dos", "da", "de", "do", "das", "pelo", "pela"
}

def extract_entities(text: str) -> dict:
    """Extrai novos alvos (Emails, IPs, Domínios, Telefones) de um texto cru via Regex."""
    if not isinstance(text, str):
        return {}

    # Regexes básicas para extração forense
    regex_ip = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    regex_email = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    regex_domain = r'(?<!@)\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'
    # Regex para telefones brasileiros: (11) 98888-7777, 11988887777, +55...
    regex_phone = r'(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?9?\d{4}[-.\s]?\d{4}'
    
    ips = set(re.findall(regex_ip, text))
    emails = set(re.findall(regex_email, text))
    domains = set(re.findall(regex_domain, text))
    phones = set(re.findall(regex_phone, text))

    # Filtros de ruído estrutural
    ips = {ip for ip in ips if not ip.startswith(("127.", "192.168.", "10.", "172.16."))}
    
    # Limpa telefones pra remover carácteres especiais pra trigger mais limpo
    phones = {re.sub(r'\D', '', p) for p in phones if len(re.sub(r'\D', '', p)) >= 10}
    
    # Filtro de ruído para domínios e e-mails (evitar nomes comuns como domínios)
    domains = {d.lower() for d in domains if d.lower() not in NOISE_WORDS and "." in d}
    emails = {e.lower() for e in emails if e.split("@")[0] not in NOISE_WORDS}
    
    return {
        "ip": list(ips),
        "email": list(emails),
        "domain": [d for d in domains if d not in ips],
        "phone": list(phones)
    }
