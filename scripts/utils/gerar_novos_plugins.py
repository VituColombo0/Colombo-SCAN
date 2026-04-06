import yaml, os

PASTA = "plugins"
os.makedirs(PASTA, exist_ok=True)
NOVOS_PLUGINS = [
    ["gallery-dl Downloader",   "🔍 Busca Reversa de Imagem", "jauderho/gallery-dl",       "{alvo}",                            "URL do perfil/galeria pra baixar:"],
    ["ExifTool Reverso",        "🔍 Busca Reversa de Imagem", "v4tech/exiftool",            "{alvo}",                            "Caminho ou URL da imagem suspeita:"],
    ["TinEye via curl",         "🔍 Busca Reversa de Imagem", "curlimages/curl",            "-s 'https://tineye.com/search?url={alvo}'", "Link direto da imagem (https://...):"],
    ["Yandex Images curl",      "🔍 Busca Reversa de Imagem", "curlimages/curl",            "-sL 'https://yandex.com/images/search?url={alvo}&rpt=imageview' | grep -o 'Found [0-9]* sites'", "Link direto da imagem:"],
    ["Imagem GPS via exif",     "🔍 Busca Reversa de Imagem", "v4tech/exiftool",            "-GPSLatitude -GPSLongitude -n {alvo}", "Caminho local ou URL da foto:"],
    ["IPInfo Geoloc",         "🌍 Geolocalização", "curlimages/curl",       "-s https://ipinfo.io/{alvo}/json",             "IP ou domínio:"],
    ["MaxMind GeoIP",         "🌍 Geolocalização", "curlimages/curl",       "-s 'https://geolocation-db.com/json/{alvo}'",  "Endereço IP:"],
    ["IP-API Lookup",         "🌍 Geolocalização", "curlimages/curl",       "-s http://ip-api.com/json/{alvo}",             "IP:"],
    ["RDAP Owner",            "🌍 Geolocalização", "curlimages/curl",       "-s https://rdap.org/ip/{alvo}",                "IP:"],
    ["Shodan InternetDB",     "🌍 Geolocalização", "curlimages/curl",       "-s https://internetdb.shodan.io/{alvo}",       "IP:"],
    ["BGP Prefix",            "🌍 Geolocalização", "curlimages/curl",       "-s https://api.bgpview.io/ip/{alvo}",          "IP:"],
    ["DNS Reverso",           "🌍 Geolocalização", "alpine",               "sh -c 'apk add -q bind-tools && host {alvo}'", "IP ou domínio:"],
    ["Traceroute",            "🌍 Geolocalização", "alpine",               "sh -c 'apk add -q traceroute && traceroute -m 15 {alvo}'", "IP ou domínio:"],
    ["ASN Lookup",            "🌍 Geolocalização", "curlimages/curl",       "-s https://api.bgpview.io/search?query_term={alvo}", "ASN ou IP:"],
    ["Abuse IPDB",            "🌍 Geolocalização", "curlimages/curl",       "-s 'https://api.abuseipdb.com/api/v2/check?ipAddress={alvo}'", "IP suspeito:"],
    ["BTC Address Info",      "💰 Rastreio de Criptomoedas", "curlimages/curl", "-s https://blockchain.info/rawaddr/{alvo}",          "Endereço Bitcoin (1xxx ou 3xxx):"],
    ["BTC Transactions",      "💰 Rastreio de Criptomoedas", "curlimages/curl", "-s https://blockchain.info/address/{alvo}",           "Endereço Bitcoin:"],
    ["ETH Address Etherscan", "💰 Rastreio de Criptomoedas", "curlimages/curl", "-s 'https://api.etherscan.io/api?module=account&action=balance&address={alvo}&tag=latest'", "Endereço ETH (0x...):"],
    ["ETH Transactions",      "💰 Rastreio de Criptomoedas", "curlimages/curl", "-s 'https://api.etherscan.io/api?module=account&action=txlist&address={alvo}&sort=desc'",   "Endereço ETH:"],
    ["Blockchair BTC",        "💰 Rastreio de Criptomoedas", "curlimages/curl", "-s https://api.blockchair.com/bitcoin/dashboards/address/{alvo}", "Endereço Bitcoin:"],
    ["LTC Lookup",            "💰 Rastreio de Criptomoedas", "curlimages/curl", "-s https://api.blockchair.com/litecoin/dashboards/address/{alvo}", "Endereço Litecoin (ltc1...):"],
    ["Crypto OSINT",          "💰 Rastreio de Criptomoedas", "alpine",          "sh -c 'echo Tipo detectado: && echo {alvo} | grep -oP \"^[0-9a-zA-Z]+\"'", "Endereço cripto (BTC/ETH/LTC):"],
    ["ExifTool PDF",          "📄 Documentos e Arquivos", "v4tech/exiftool",      "{alvo}",                  "Caminho do PDF ou URL:"],
    ["Strings Doc",           "📄 Documentos e Arquivos", "alpine",               "strings {alvo}",          "Caminho do arquivo:"],
    ["File Type Detect",      "📄 Documentos e Arquivos", "alpine",               "file {alvo}",             "Caminho:"],
    ["HexDump Cabeçalho",     "📄 Documentos e Arquivos", "alpine",               "sh -c 'hexdump -C {alvo} | head -n 20'", "Caminho:"],
    ["Binwalk Doc",           "📄 Documentos e Arquivos", "kurobeats/binwalk",    "{alvo}",                  "Caminho do documento:"],
    ["Mat2 Metadata",         "📄 Documentos e Arquivos", "secsi/mat2",           "show {alvo}",             "Caminho do PDF/Word:"],
    ["SHA256 Hash",           "📄 Documentos e Arquivos", "alpine",               "sh -c 'sha256sum {alvo}'", "Caminho do arquivo:"],
    ["MD5 Hash",              "📄 Documentos e Arquivos", "alpine",               "sh -c 'md5sum {alvo}'",   "Caminho do arquivo:"],
    ["ffprobe Metadados",     "🎙️ Áudio e Vídeo Forense", "jrottenberg/ffmpeg",  "sh -c 'ffprobe -v quiet -print_format json -show_format -show_streams {alvo}'", "Caminho ou URL do vídeo/áudio:"],
    ["MediaInfo",             "🎙️ Áudio e Vídeo Forense", "jlesage/mediainfo",   "{alvo}",                  "Caminho do arquivo de mídia:"],
    ["ExifTool Video",        "🎙️ Áudio e Vídeo Forense", "v4tech/exiftool",     "{alvo}",                  "Caminho ou URL do vídeo/foto:"],
    ["Strings Audio",         "🎙️ Áudio e Vídeo Forense", "alpine",              "strings {alvo} | head -50", "Caminho do arquivo:"],
    ["File Hash Video",       "🎙️ Áudio e Vídeo Forense", "alpine",              "sh -c 'sha256sum {alvo} && md5sum {alvo}'", "Caminho do arquivo:"],
    ["snscrape Twitter",      "💬 Redes Sociais", "curlimages/curl", "-s 'https://nitter.net/{alvo}/rss'",                           "Username do Twitter/X:"],
    ["Reddit User",           "💬 Redes Sociais", "curlimages/curl", "-s 'https://www.reddit.com/user/{alvo}/about.json' -A Mozilla", "Username do Reddit:"],
    ["GitHub User",           "💬 Redes Sociais", "curlimages/curl", "-s https://api.github.com/users/{alvo}",                       "Username do GitHub:"],
    ["GitHub Repos",          "💬 Redes Sociais", "curlimages/curl", "-s https://api.github.com/users/{alvo}/repos",                 "Username do GitHub:"],
    ["Instagram OEmbed",      "💬 Redes Sociais", "curlimages/curl", "-s 'https://www.instagram.com/{alvo}/?__a=1' -A Mozilla",      "Username do Instagram:"],
    ["TikTok OEmbed",         "💬 Redes Sociais", "curlimages/curl", "-s 'https://www.tiktok.com/@{alvo}' -A Mozilla | grep -o 'followerCount[^,]+'", "Username do TikTok:"],
    ["Telegram Channel",      "💬 Redes Sociais", "curlimages/curl", "-sL 'https://t.me/{alvo}' | grep -o 'members[^<]+'",           "Username do canal Telegram:"],
    ["OnionSearch DuckDuck",  "🌑 Dark Web / Onion", "alpine", "sh -c 'wget -qO- https://html.duckduckgo.com/html/?q=site:.onion+{alvo} | grep -o \"[a-z0-9]*\\.onion\"'", "Termo de busca (ex: nome da pessoa):"],
    ["Ahmia Onion Search",    "🌑 Dark Web / Onion", "curlimages/curl", "-s 'https://ahmia.fi/search/?q={alvo}'", "Termo de busca:"],
    ["OnionSearch Haystack",  "🌑 Dark Web / Onion", "curlimages/curl", "-s 'https://haystack.mobi/search?q={alvo}'", "Termo:"],
    ["Shodan Host",           "📡 Shodan / Dispositivos IoT", "curlimages/curl", "-s https://internetdb.shodan.io/{alvo}", "IP ou domínio:"],
    ["Censys IP",             "📡 Shodan / Dispositivos IoT", "curlimages/curl", "-s 'https://search.censys.io/api/v1/view/ipv4/{alvo}'", "IP:"],
    ["BinaryEdge",            "📡 Shodan / Dispositivos IoT", "curlimages/curl", "-s 'https://app.binaryedge.io/services/query?query={alvo}'", "IP:"],
    ["Fofa API",              "📡 Shodan / Dispositivos IoT", "curlimages/curl", "-s 'https://fofa.info/api/v1/search/all?qbase64={alvo}'", "Query em base64:"],
    ["MISP Feed Check",       "📡 Shodan / Dispositivos IoT", "curlimages/curl", "-s 'https://otx.alienvault.com/api/v1/indicators/IPv4/{alvo}'", "IP:"],
]

for item in NOVOS_PLUGINS:
    nome = item[0].lower().replace(' ', '_').replace('/', '').replace('(','').replace(')','') + ".yaml"
    caminho = os.path.join(PASTA, nome)

    config = {
        "name": item[0],
        "category": item[1],
        "description": item[0] + " plugin",
        "type": "docker",
        "image": item[2],
        "command": item[3],
        "inputs": [{"id": "alvo", "prompt": item[4]}]
    }

    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

print(f"✅ {len(NOVOS_PLUGINS)} novos plugins criados!")
