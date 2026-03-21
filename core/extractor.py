import re

def extract_entities(text: str) -> dict:
    """Extrai novos alvos (Emails, IPs, Domínios, Telefones) de um texto cru via Regex."""
    if not isinstance(text, str):
        return {}

    # Regexes básicas para extração forense
    regex_ip = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    regex_email = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    regex_domain = r'(?<!@)\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'
    
    ips = set(re.findall(regex_ip, text))
    emails = set(re.findall(regex_email, text))
    domains = set(re.findall(regex_domain, text))

    # Filtros de ruído estrutural (exclui sub-redes locais e strings comuns)
    ips = {ip for ip in ips if not ip.startswith(("127.", "192.168.", "10.", "172.16."))}
    
    return {
        "ip": list(ips),
        "email": list(emails),
        "domain": [d for d in domains if d not in ips] # evita IPs sendo classificados como domínios
    }
