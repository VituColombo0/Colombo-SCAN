from urllib.parse import quote
from core.entities import EntityType

def generate_dorks(value: str, e_type: EntityType) -> list[dict]:
    """Generates lethal Google Dorks / Queries based on the entity type."""
    dorks = []
    
    if e_type == EntityType.EMAIL:
        dorks.append({"title": "Pastebin Leaks", "query": f'site:pastebin.com "{value}"'})
        dorks.append({"title": "Google Docs/Sheets", "query": f'site:docs.google.com "{value}"'})
        dorks.append({"title": "Directory Listings", "query": f'intitle:"index of" "{value}"'})
    
    elif e_type == EntityType.PHONE:
        # Pega so os numeros ignorando simbolos pro regex amplo
        num_limpo = ''.join(filter(str.isdigit, value))
        dorks.append({"title": "PDFs e Currículos", "query": f'filetype:pdf "{value}" OR "{num_limpo}"'})
        dorks.append({"title": "Processos Jurídicos", "query": f'site:jusbrasil.com.br "{value}" OR "{num_limpo}"'})
    
    elif e_type == EntityType.USERNAME:
        dorks.append({"title": "Redes Sociais Niche", "query": f'"{value}" -site:youtube.com -site:facebook.com'})
        dorks.append({"title": "Listas de Senhas (Git)", "query": f'site:github.com "{value}" password OR token'})

    elif e_type == EntityType.PERSON:
        dorks.append({"title": "LinkedIn Cross-Match", "query": f'site:linkedin.com/in "{value}"'})
        dorks.append({"title": "Notícias/Diário Oficial", "query": f'"{value}" (fraude OR processo OR jusbrasil OR diario oficial)'})

    elif e_type == EntityType.DOMAIN:
        dorks.append({"title": "Subdomínios Expostos", "query": f'site:{value} -www'})
        dorks.append({"title": "Arquivos Sensíveis", "query": f'site:{value} filetype:pdf OR filetype:xls OR filetype:doc OR filetype:sql'})
        dorks.append({"title": "Painéis Admin", "query": f'site:{value} inurl:admin OR inurl:login OR inurl:painel'})

    elif e_type == EntityType.IP:
        dorks.append({"title": "Shodan", "query": f'site:shodan.io "{value}"'})
        dorks.append({"title": "Serviços Expostos", "query": f'"{value}" (port OR open OR service OR banner)'})
        dorks.append({"title": "Registros de Abuse", "query": f'"{value}" (abuse OR report OR blacklist OR spam)'})

    elif e_type == EntityType.CPF:
        num_limpo = ''.join(filter(str.isdigit, value))
        dorks.append({"title": "Processos Judiciais", "query": f'site:jusbrasil.com.br "{value}" OR "{num_limpo}"'})
        dorks.append({"title": "Documentos Públicos", "query": f'filetype:pdf "{value}" OR "{num_limpo}"'})

    elif e_type == EntityType.CNPJ:
        num_limpo = ''.join(filter(str.isdigit, value))
        dorks.append({"title": "Receita Federal", "query": f'"{value}" OR "{num_limpo}" (receita federal OR cnpj)'})
        dorks.append({"title": "Processos e Fraudes", "query": f'"{value}" OR "{num_limpo}" (processo OR fraude OR irregularidade)'})

    # Wrap up into actionable URLs
    result = []
    for d in dorks:
        url = f"https://www.google.com/search?q={quote(d['query'])}"
        result.append({
            "title": d["title"],
            "query": d["query"],
            "url": url
        })
    return result
