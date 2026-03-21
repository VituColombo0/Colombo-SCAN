import os
import yaml

PLUGIN_DIR = "plugins"
os.makedirs(PLUGIN_DIR, exist_ok=True)

novos_plugins = [
    {"name": "ghunt", "category": "📧 Análise de Emails", "description": "OSINT focado em contas do Google (Fotos, Maps, YouTube).", "command": "docker run --rm -it mxrch/ghunt email {alvo}", "inputs": [{"id": "alvo", "prompt": "Email alvo:"}], "timeout": 60, "safe": True},
    {"name": "holehe", "category": "📧 Análise de Emails", "description": "Verifica se um email está registrado em +120 sites (Twitter, Instagram, etc).", "command": "docker run --rm megadose/holehe {alvo}", "inputs": [{"id": "alvo", "prompt": "Email alvo:"}], "timeout": 60, "safe": True},
    {"name": "mosint", "category": "📧 Análise de Emails", "description": "Ferramenta Go automatizada para OSINT em e-mails (brechas, domínios, etc).", "command": "docker run --rm alpkeskin/mosint {alvo}", "inputs": [{"id": "alvo", "prompt": "Email alvo:"}], "timeout": 60, "safe": True},
    {"name": "theharvester", "category": "📧 Análise de Emails", "description": "Coleta de e-mails, subdomínios, hosts e IPs de diversas fontes públicas.", "command": "docker run --rm secsi/theharvester -d {alvo} -b all", "inputs": [{"id": "alvo", "prompt": "Domínio alvo (ex: empresa.com):"}], "timeout": 90, "safe": True},
    {"name": "h8mail", "category": "📧 Análise de Emails", "description": "Busca senhas vazadas de emails em bancos de dados remotos.", "command": "docker run --rm khast3x/h8mail -t {alvo}", "inputs": [{"id": "alvo", "prompt": "Email alvo:"}], "timeout": 60, "safe": True},
    {"name": "socialscan", "category": "👤 Identidades e Usernames", "description": "Busca extremamente rápida de usernames e emails em redes sociais.", "command": "docker run --rm msoedov/socialscan {alvo}", "inputs": [{"id": "alvo", "prompt": "Username ou email alvo:"}], "timeout": 45, "safe": True},
    {"name": "blackbird", "category": "👤 Identidades e Usernames", "description": "Busca rápida e moderna de contas por username em 130 sites.", "command": "docker run --rm p1ngul1n0/blackbird -u {alvo}", "inputs": [{"id": "alvo", "prompt": "Username alvo:"}], "timeout": 60, "safe": True},
    {"name": "whatsmyname", "category": "👤 Identidades e Usernames", "description": "Busca enumeração de usuários em milhares de sites.", "command": "curl -s 'https://whatsmyname.app/api/search?q={alvo}' | grep -o '\"uri\":\"[^\"]*\"'", "inputs": [{"id": "alvo", "prompt": "Username alvo:"}], "timeout": 45, "safe": True},
    {"name": "enola", "category": "👤 Identidades e Usernames", "description": "OSINT social rápido usando web scraping e APIs.", "command": "docker run --rm enola-osint {alvo}", "inputs": [{"id": "alvo", "prompt": "Username alvo:"}], "timeout": 60, "safe": True},
    {"name": "spiderfoot", "category": "🌐 Redes e IPs", "description": "Plataforma OSINT massiva automatizada (+100 fontes).", "command": "docker run --rm smicallef/spiderfoot -s {alvo} -q", "inputs": [{"id": "alvo", "prompt": "Alvo (IP, domínio, email):"}], "timeout": 120, "safe": True},
    {"name": "recon-ng-cli", "category": "🌐 Redes e IPs", "description": "Framework de reconhecimento modular completo.", "command": "docker run --rm mclarkson/recon-ng -C 'add domains {alvo}; run'", "inputs": [{"id": "alvo", "prompt": "Domínio alvo:"}], "timeout": 90, "safe": True},
    {"name": "amass", "category": "🌐 Redes e IPs", "description": "Mapeamento profundo de superfície de ataque e subdomínios.", "command": "docker run --rm caffix/amass enum -d {alvo}", "inputs": [{"id": "alvo", "prompt": "Domínio alvo:"}], "timeout": 120, "safe": True},
    {"name": "dnsdumpster-cli", "category": "🌐 Redes e IPs", "description": "Pesquisa massiva de DNS e descobrimento de hosts.", "command": "curl -s 'https://api.hackertarget.com/hostsearch/?q={alvo}'", "inputs": [{"id": "alvo", "prompt": "Domínio ou IP alvo:"}], "timeout": 45, "safe": True},
    {"name": "photon", "category": "🌐 Redes e IPs", "description": "Crawler OSINT ultra rápido que extrai URLs, emails, arquivos, chaves cloud.", "command": "docker run --rm s0md3v/photon -u {alvo}", "inputs": [{"id": "alvo", "prompt": "URL alvo:"}], "timeout": 90, "safe": True},
    {"name": "shodan-cli", "category": "💻 IoT e Dispositivos", "description": "Busca o alvo no Shodan (o motor de busca para a Internet das Coisas).", "command": "curl -s 'https://internetdb.shodan.io/{alvo}'", "inputs": [{"id": "alvo", "prompt": "IP ou domínio alvo:"}], "timeout": 30, "safe": True},
    {"name": "censys-cli", "category": "💻 IoT e Dispositivos", "description": "Busca certificados SSL, hosts expostos e servidores via Censys.", "command": "curl -A 'Colombo Scanner' -s 'https://search.censys.io/api/v2/hosts/{alvo}'", "inputs": [{"id": "alvo", "prompt": "IP alvo:"}], "timeout": 40, "safe": True},
    {"name": "zoomeye", "category": "💻 IoT e Dispositivos", "description": "Busca informações de ciberespaço e infraestrutura no ZoomEye.", "command": "curl -s 'https://api.zoomeye.org/host/search?query={alvo}'", "inputs": [{"id": "alvo", "prompt": "IP ou query alvo:"}], "timeout": 40, "safe": True},
    {"name": "mac-vendor-lookup", "category": "💻 IoT e Dispositivos", "description": "Descobre o fabricante de um dispositivo baseado no endereço MAC.", "command": "curl -s 'https://api.macvendors.com/{alvo}'", "inputs": [{"id": "alvo", "prompt": "Endereço MAC alvo (ex: 00:1A:2B...):"}], "timeout": 20, "safe": True},
    {"name": "receitaws", "category": "🏢 Corporate & CNPJ", "description": "Busca detalhada CNPJ na Receita Federal (Brasil).", "command": "curl -s 'https://receitaws.com.br/v1/cnpj/{alvo}' | jq '.'", "inputs": [{"id": "alvo", "prompt": "CNPJ alvo (apenas números):"}], "timeout": 30, "safe": True},
    {"name": "brasilapi-cnpj", "category": "🏢 Corporate & CNPJ", "description": "Dados da empresa via BrasilAPI (Quadro de Sócios, CNAE, Endereço).", "command": "curl -s 'https://brasilapi.com.br/api/cnpj/v1/{alvo}' | jq '.'", "inputs": [{"id": "alvo", "prompt": "CNPJ alvo (apenas números):"}], "timeout": 30, "safe": True},
    {"name": "minhareceita", "category": "🏢 Corporate & CNPJ", "description": "Consulta de dados públicos de empresas do Brasil.", "command": "curl -s 'https://minhareceita.org/{alvo}' | jq '.'", "inputs": [{"id": "alvo", "prompt": "CNPJ alvo:"}], "timeout": 30, "safe": True},
    {"name": "opencorporates", "category": "🏢 Corporate & CNPJ", "description": "Maior banco aberto de dados corporativos mundiais.", "command": "curl -s 'https://api.opencorporates.com/v0.4/companies/search?q={alvo}'", "inputs": [{"id": "alvo", "prompt": "Nome da empresa:"}], "timeout": 40, "safe": True},
    {"name": "sinesp-api", "category": "🚗 Veículos e Placas", "description": "Simulação de busca SINESP para dados básicos de placa (Modelo, Ano, Roubo).", "command": "curl -s 'https://api.placafipe.com/v2/placa/{alvo}'", "inputs": [{"id": "alvo", "prompt": "Placa do Veículo:"}], "timeout": 30, "safe": True},
    {"name": "brasilapi-tabela-fipe", "category": "🚗 Veículos e Placas", "description": "Busca valor e informações FIPE de uma placa indiretamente (se db tiver).", "command": "curl -s 'https://brasilapi.com.br/api/fipe/preco/v1/{alvo}'", "inputs": [{"id": "alvo", "prompt": "Código FIPE ou Placa:"}], "timeout": 30, "safe": True},
    {"name": "vin-decoder", "category": "🚗 Veículos e Placas", "description": "Consulta internacional de Chassis (VIN).", "command": "curl -s 'https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{alvo}?format=json'", "inputs": [{"id": "alvo", "prompt": "CHASSI (VIN) do veículo:"}], "timeout": 30, "safe": True},
    {"name": "flight-tracker-api", "category": "✈️ Rastreador de Voos", "description": "Busca status do voo e rotas (baseado no número do voo).", "command": "curl -s 'https://flightradar24-sim.colombo.com/api/flight/{alvo}'", "inputs": [{"id": "alvo", "prompt": "Número do voo (ex: LA8100):"}], "timeout": 30, "safe": True},
    {"name": "adsb-exchange", "category": "✈️ Rastreador de Voos", "description": "Busca não-filtrada de atividade aérea e histórico do avião.", "command": "curl -s 'https://api.adsb.lol/api/0/flight/{alvo}'", "inputs": [{"id": "alvo", "prompt": "Número do voo ou Callsign:"}], "timeout": 30, "safe": True},
    {"name": "have-i-been-pwned", "category": "🔐 Vazamentos Profundos", "description": "Verifica se a conta sofreu algum vazamento massivo documentado.", "command": "curl -s -A 'Colombo-OSINT-Scanner' 'https://haveibeenpwned.com/api/v3/breachedaccount/{alvo}'", "inputs": [{"id": "alvo", "prompt": "Email ou Username alvo:"}], "timeout": 30, "safe": True},
    {"name": "leaklooker", "category": "🔐 Vazamentos Profundos", "description": "Verifica instâncias expostas e senhas padrão no Shodan, Firebase, etc.", "command": "docker run --rm xilox/leaklooker -k {alvo}", "inputs": [{"id": "alvo", "prompt": "Palavra-chave/Alvo:"}], "timeout": 90, "safe": True},
    {"name": "dehashed-api", "category": "🔐 Vazamentos Profundos", "description": "Busca credenciais em texto claro (requer key, simulação).", "command": "curl -s 'https://api.dehashed.com/search?query={alvo}'", "inputs": [{"id": "alvo", "prompt": "Email ou IP alvo:"}], "timeout": 40, "safe": True},
    {"name": "wigle-wifi", "category": "🌍 Geolocalização", "description": "Mapeia redes WiFi baseadas em MAC Address ou SSID, ótimo para GEO Intel.", "command": "curl -s 'https://api.wigle.net/api/v2/network/search?ssid={alvo}'", "inputs": [{"id": "alvo", "prompt": "Nome da Rede WiFi (SSID):"}], "timeout": 45, "safe": True},
    {"name": "creepy-sim", "category": "🌍 Geolocalização", "description": "Geolocalização usando tweets geolocalizados e metadados de imagens.", "command": "echo 'Simulação Creepy Geo-Intel para {alvo} - Extraindo GEO tags de repositórios conhecidos'", "inputs": [{"id": "alvo", "prompt": "Username ou link:"}], "timeout": 20, "safe": True},
]

count = 0
for plugin in novos_plugins:
    nome_arquivo = f"{plugin['name'].replace(' ', '_').lower()}.yaml"
    caminho = os.path.join(PLUGIN_DIR, nome_arquivo)
    
    if os.path.exists(caminho):
        continue
        
    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(plugin, f, allow_unicode=True, sort_keys=False)
    count += 1

print(f"✅ Sucesso! {count} novos plugins especializados gerados nas categorias:")
print("- 💻 IoT e Dispositivos\n- 🏢 Corporate & CNPJ\n- 🚗 Veículos e Placas\n- ✈️ Rastreador de Voos\n- Novas integrações de E-mail, Redes e Vazamentos!")
