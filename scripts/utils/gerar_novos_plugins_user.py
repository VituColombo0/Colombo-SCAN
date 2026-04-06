import os
import yaml

PLUGIN_DIR = "plugins"
os.makedirs(PLUGIN_DIR, exist_ok=True)

novos_plugins = [
    {"name": "greynoise", "category": "🌐 Redes e IPs", "description": "Busca inteligência sobre IPs ruidosos e atividades de scan na internet.", "command": "curl -s 'https://api.greynoise.io/v3/community/{alvo}'", "inputs": [{"id": "alvo", "prompt": "IP alvo:"}], "timeout": 30, "safe": True},
    {"name": "onyphe", "category": "💻 IoT e Dispositivos", "description": "Busca informações sobre IPs e dispositivos no cyber defense engine Onyphe.", "command": "curl -s 'https://www.onyphe.io/api/v2/simple/search?term={alvo}'", "inputs": [{"id": "alvo", "prompt": "IP ou Domínio alvo:"}], "timeout": 30, "safe": True},
    {"name": "leakix", "category": "🔐 Vazamentos Profundos", "description": "Buscador de informações sobre infraestrutura esquecida e exposta.", "command": "curl -s 'https://leakix.net/api/public/host/{alvo}'", "inputs": [{"id": "alvo", "prompt": "IP ou subrede alvo:"}], "timeout": 30, "safe": True},
    {"name": "criminalip", "category": "🌐 Redes e IPs", "description": "Assessment de risco e inventário de assets sobre o IP.", "command": "curl -s 'https://api.criminalip.io/v1/asset/ip/report?ip={alvo}'", "inputs": [{"id": "alvo", "prompt": "IP alvo:"}], "timeout": 35, "safe": True},
    {"name": "netlas", "category": "🌐 Redes e IPs", "description": "Plataforma de descoberta de superfície de ataque e inteligência.", "command": "curl -s 'https://app.netlas.io/api/responses_filter/?q={alvo}'", "inputs": [{"id": "alvo", "prompt": "IP ou Domínio alvo:"}], "timeout": 35, "safe": True},
    {"name": "securitytrails", "category": "🕸️ Mapeamento de Superfície", "description": "Plataforma de dados sobre domínios, DNS histórico e subdomínios.", "command": "curl -s 'https://api.securitytrails.com/v1/domain/{alvo}/subdomains'", "inputs": [{"id": "alvo", "prompt": "Domínio alvo:"}], "timeout": 45, "safe": True},
    {"name": "dorksearch", "category": "🧠 Inteligência de Busca", "description": "Pesquisa automatizada via Google Dorks.", "command": "echo 'Acesse para utilizar dorks pré-prontas sobre o alvo: https://dorksearch.com/?q={alvo}'", "inputs": [{"id": "alvo", "prompt": "Termo ou Domínio:"}], "timeout": 10, "safe": True},
    {"name": "exploit-db", "category": "🛡️ DevSecOps & Vulnerabilidades", "description": "Pesquisa sobre exploits conhecidos em serviços identificados.", "command": "docker run --rm bitnami/searchsploit {alvo}", "inputs": [{"id": "alvo", "prompt": "Nome do serviço/versão (ex: apache 2.4):"}], "timeout": 60, "safe": True},
    {"name": "pulsedive", "category": "🌐 Redes e IPs", "description": "Motor de busca sobre ameaças e inteligência cibernética.", "command": "curl -s 'https://pulsedive.com/api/info.php?indicator={alvo}'", "inputs": [{"id": "alvo", "prompt": "IP, Domínio ou Hash alvo:"}], "timeout": 30, "safe": True},
    {"name": "grayhatwarfare", "category": "🔐 Vazamentos Profundos", "description": "Buscador de baldes abertos da AWS/S3 e Azure.", "command": "curl -s 'https://api.grayhatwarfare.com/files/search/{alvo}'", "inputs": [{"id": "alvo", "prompt": "Keyword alvo:"}], "timeout": 30, "safe": True},
    {"name": "polyswarm", "category": "🛡️ DevSecOps & Vulnerabilidades", "description": "Marketspace de detecção de ameaças de malware via hash.", "command": "curl -s 'https://api.polyswarm.network/v2/search/hash/sha256/{alvo}'", "inputs": [{"id": "alvo", "prompt": "Hash SHA256 alvo:"}], "timeout": 30, "safe": True},
    {"name": "urlscan", "category": "🕸️ Mapeamento de Superfície", "description": "Scan completo de sites, análise de requests, imagens e tecnologias.", "command": "curl -s 'https://urlscan.io/api/v1/search/?q=domain:{alvo}'", "inputs": [{"id": "alvo", "prompt": "Domínio ou URL alvo:"}], "timeout": 45, "safe": True},
    {"name": "vulners", "category": "🛡️ DevSecOps & Vulnerabilidades", "description": "Base de dados e pesquisa de vulnerabilidades sobre tecnologias específicas.", "command": "curl -s 'https://vulners.com/api/v3/search/lucene/?query={alvo}'", "inputs": [{"id": "alvo", "prompt": "Termo da busca de vuln:"}], "timeout": 30, "safe": True},
    {"name": "publicwww", "category": "🧠 Inteligência de Busca", "description": "Buscador de trechos de código fonte no corpo das páginas web.", "command": "curl -s 'https://publicwww.com/websites/{alvo}/?export=csv'", "inputs": [{"id": "alvo", "prompt": "Snippet de código ou ID alvo:"}], "timeout": 40, "safe": True},
    {"name": "intelx", "category": "🔐 Vazamentos Profundos", "description": "IntelligenceX: pesquisa sobre vazamentos de dados, domínios, etc.", "command": "echo 'Ferramenta IntelligenceX requer Auth ou console. Acesse: https://intelx.io/?s={alvo}'", "inputs": [{"id": "alvo", "prompt": "Email, IP, Domínio ou Bitcoin address:"}], "timeout": 15, "safe": True},
    {"name": "grep_app", "category": "🛡️ DevSecOps & Vulnerabilidades", "description": "Busca massiva por código em repositórios do GitHub.", "command": "curl -s 'https://grep.app/api/search?q={alvo}'", "inputs": [{"id": "alvo", "prompt": "Padrão de código regex ou termo:"}], "timeout": 30, "safe": True},
    {"name": "packetstorm", "category": "🛡️ DevSecOps & Vulnerabilidades", "description": "Recursos de segurança e base de dados de vulnerabilidades.", "command": "echo 'Busca em PacketStorm: https://packetstormsecurity.com/search/?q={alvo}'", "inputs": [{"id": "alvo", "prompt": "Termo de busca vazamento/vuln:"}], "timeout": 10, "safe": True},
    {"name": "searchcode", "category": "🧠 Inteligência de Busca", "description": "Motor de busca de APIs, bibliotecas e trechos de código livre.", "command": "curl -s 'https://searchcode.com/api/codesearch_I/?q={alvo}'", "inputs": [{"id": "alvo", "prompt": "Termo de busca código:"}], "timeout": 30, "safe": True},
    {"name": "dnsdb", "category": "🕸️ Mapeamento de Superfície", "description": "Pesquisas sobre infraestrutura de DNS histórica Farsight.", "command": "curl -s 'https://api.dnsdb.info/lookup/rrset/name/{alvo}'", "inputs": [{"id": "alvo", "prompt": "Domínio alvo:"}], "timeout": 30, "safe": True},
    {"name": "fullhunt", "category": "🕸️ Mapeamento de Superfície", "description": "Plataforma de mapeamento contínuo de superfície de ataque.", "command": "curl -s 'https://fullhunt.io/api/v1/domain/{alvo}/details'", "inputs": [{"id": "alvo", "prompt": "Domínio alvo:"}], "timeout": 30, "safe": True},
    {"name": "virustotal", "category": "🛡️ DevSecOps & Vulnerabilidades", "description": "Ferramenta suprema de detecção de vírus em arquivos/URLs/IPs.", "command": "curl -s 'https://www.virustotal.com/api/v3/search?query={alvo}'", "inputs": [{"id": "alvo", "prompt": "IP, Domínio, Hash ou URL alvo:"}], "timeout": 30, "safe": True}
]

count = 0
for plugin in novos_plugins:
    nome_arquivo = f"{plugin['name'].replace(' ', '_').lower()}.yaml"
    caminho = os.path.join(PLUGIN_DIR, nome_arquivo)
    
    exists = False
    for root, dirs, files in os.walk(PLUGIN_DIR):
        if nome_arquivo in files:
            exists = True
            break
            
    if exists:
        continue
        
    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(plugin, f, allow_unicode=True, sort_keys=False)
    count += 1

print(f"Sucesso! {count} novos plugins gerados baseados na lista fornecida.")
