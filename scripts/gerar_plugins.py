import yaml
import os

ferramentas_compactas = [
    ["Nmap Rapido", "🌐 Redes e IPs", "instrumentisto/nmap", "-F {alvo}"],
    ["Nmap Agressivo", "🌐 Redes e IPs", "instrumentisto/nmap", "-A -T4 {alvo}"],
    ["Whois", "🌐 Redes e IPs", "bennetimo/whois", "{alvo}"],
    ["Subfinder", "🌐 Redes e IPs", "projectdiscovery/subfinder", "-d {alvo} -silent"],
    ["Amass", "🌐 Redes e IPs", "caffix/amass", "enum -d {alvo}"],
    ["Nuclei", "🌐 Redes e IPs", "projectdiscovery/nuclei", "-u {alvo} -silent"],
    ["Naabu", "🌐 Redes e IPs", "projectdiscovery/naabu", "-host {alvo}"],
    ["WhatWeb", "🌐 Redes e IPs", "secsi/whatweb", "{alvo}"],
    ["Dirb", "🌐 Redes e IPs", "secsi/dirb", "{alvo}"],
    ["Nikto", "🌐 Redes e IPs", "secsi/nikto", "-h {alvo}"],
    ["Sherlock", "👤 Identidades e Usernames", "sherlock/sherlock", "{alvo}"],
    ["Maigret", "👤 Identidades e Usernames", "soxoj/maigret", "{alvo}"],
    ["WhatsMyName", "👤 Identidades e Usernames", "secsi/whatsmyname", "-u {alvo}"],
    ["BlackWidow", "👤 Identidades e Usernames", "michelin/blackwidow", "-d {alvo}"],
    ["Photon", "👤 Identidades e Usernames", "secsi/photon", "-u {alvo}"],
    ["SocialAnalyzer", "👤 Identidades e Usernames", "qeeqbox/social-analyzer", "--username {alvo}"],
    ["Twint Scrape", "👤 Identidades e Usernames", "wint3rmute/twint", "-u {alvo}"],
    ["OsintGram", "👤 Identidades e Usernames", "secsi/osintgram", "{alvo} --info"],
    ["GHunt Google", "👤 Identidades e Usernames", "mxrch/ghunt", "email {alvo}"],
    ["GitRecon", "👤 Identidades e Usernames", "alpine", "sh -c 'wget -qO- https://api.github.com/users/{alvo}/events/public | grep -o repo'"],
    ["Holehe", "📧 Análise de Emails", "megaron/holehe", "{alvo}"],
    ["TheHarvester", "📧 Análise de Emails", "secsi/theharvester", "-d {alvo} -b all"],
    ["Infoga", "📧 Análise de Emails", "secsi/infoga", "-d {alvo} -s all"],
    ["H8Mail Leaks", "📧 Análise de Emails", "shmilylty/h8mail", "-t {alvo}"],
    ["Buster", "📧 Análise de Emails", "secsi/buster", "-e {alvo}"],
    ["Hubble", "📧 Análise de Emails", "khast3x/hubble", "{alvo}"],
    ["MX Lookup", "📧 Análise de Emails", "alpine", "sh -c 'apk add --no-cache bind-tools >/dev/null && dig +short MX {alvo}'"],
    ["HaveIBeenPwned API", "📧 Análise de Emails", "curlimages/curl", "-s -A 'Mozilla' https://haveibeenpwned.com/api/v3/breachedaccount/{alvo}"],
    ["SMTP Enum", "📧 Análise de Emails", "alpine", "sh -c 'apk add nmap >/dev/null && nmap --script smtp-enum-users.nse -p 25 {alvo}'"],
    ["Hunter Pattern", "📧 Análise de Emails", "curlimages/curl", "-s 'https://api.hunter.io/v2/domain-search?domain={alvo}'"],
    ["ExifTool", "🖼️ Análise de Imagens", "v4tech/exiftool", "{alvo}"],
    ["Binwalk", "🖼️ Análise de Imagens", "kurobeats/binwalk", "{alvo}"],
    ["Mat2", "🖼️ Análise de Imagens", "secsi/mat2", "show {alvo}"],
    ["Steghide", "🖼️ Análise de Imagens", "hpsj/steghide", "info {alvo} < /dev/null"],
    ["Strings Extrator", "🖼️ Análise de Imagens", "alpine", "strings {alvo}"],
    ["HexDump Core", "🖼️ Análise de Imagens", "alpine", "sh -c 'hexdump -C {alvo} | head -n 50'"],
    ["ImageMagick Verbose", "🖼️ Análise de Imagens", "dpokidov/imagemagick", "identify -verbose {alvo}"],
    ["Tesseract OCR", "🖼️ Análise de Imagens", "jamesbrink/tesseract-ocr", "{alvo} stdout"],
    ["Base64 Decoder", "🖼️ Análise de Imagens", "alpine", "sh -c 'base64 -d {alvo} 2>/dev/null | head -c 200'"],
    ["File Signatures", "🖼️ Análise de Imagens", "alpine", "file {alvo}"],
    ["PhoneInfoga", "📱 Inteligência de Telefones", "sundowndev/phoneinfoga", "scan -n {alvo}"],
    ["Ignorant Social", "📱 Inteligência de Telefones", "secsi/ignorant", "{alvo}"],
    ["Email2Phone", "📱 Inteligência de Telefones", "martinvigo/email2phonenumber", "scrape -e {alvo} -v"],
    ["Truecaller API", "📱 Inteligência de Telefones", "curlimages/curl", "-s 'https://api.truecaller.com/v1.0/search?q={alvo}'"],
    ["WhatsApp Check", "📱 Inteligência de Telefones", "alpine", "sh -c 'wget -qO- \"https://wa.me/{alvo}\" | grep -Eo \"[A-Za-z0-9 ]+ usa o WhatsApp\" || echo \"Sem Whats\"'"],
    ["WhatsApp Avatar", "📱 Inteligência de Telefones", "alpine", "sh -c 'wget -qO- \"https://wa.me/{alvo}\" | grep -Eo \"https://pps.whatsapp.net[^\"]+\"'"],
    ["Shodan Phone", "📱 Inteligência de Telefones", "curlimages/curl", "-s \"https://internetdb.shodan.io/search?query={alvo}\""],
    ["Local Vcard Parser", "📱 Inteligência de Telefones", "alpine", "sh -c 'grep -i \"{alvo}\" /home/*.vcf 2>/dev/null || echo \"Sem vCard\"'"],
    ["Carrier Lookup", "📱 Inteligência de Telefones", "alpine", "sh -c 'echo \"Consultando Blocos Anatel para: {alvo}...\"'"],
    ["DDI Parser", "📱 Inteligência de Telefones", "alpine", "sh -c 'echo \"Limpando telefone:\" && echo {alvo} | sed -E \"s/[^0-9]//g\"'"],
    ["TruffleHog Git", "🔐 Vazamentos Profundos", "trufflesecurity/trufflehog", "github --repo {alvo}"],
    ["TruffleHog S3", "🔐 Vazamentos Profundos", "trufflesecurity/trufflehog", "s3 --bucket {alvo}"],
    ["GitLeaks Local", "🔐 Vazamentos Profundos", "zricethezav/gitleaks", "detect --source {alvo} -v"],
    ["WPScan Admin Leak", "🔐 Vazamentos Profundos", "wpscanteam/wpscan", "--url {alvo} -e u,vp"],
    ["SqlMap Dumps", "🔐 Vazamentos Profundos", "sqlmapproject/sqlmap", "-u {alvo} --batch --dbs"],
    ["S3Scanner", "🔐 Vazamentos Profundos", "jakejarvis/s3scanner", "{alvo}"],
    ["ZAP Web Scan", "🔐 Vazamentos Profundos", "owasp/zap2docker-stable", "zap-baseline.py -t {alvo}"],
    ["HTTPX Status", "🔐 Vazamentos Profundos", "projectdiscovery/httpx", "-u {alvo} -sc -title"],
    ["Pastebin Leaks", "🔐 Vazamentos Profundos", "alpine", "sh -c 'wget -qO- \"https://html.duckduckgo.com/html/?q=site:pastebin.com+\\\"{alvo}\\\"\" | grep -o \"pastebin.com/.*\"'"],
    ["Jq Json Leaks", "🔐 Vazamentos Profundos", "imega/jq", "'.[] | select(has(\"{alvo}\"))' /tmp/alvo.tmp"]
]

import os, yaml
PASTA = "plugins"
os.makedirs(PASTA, exist_ok=True)

for item in ferramentas_compactas:
    nome = item[0].lower().replace(' ', '_').replace('/', '') + ".yaml"
    caminho = os.path.join(PASTA, nome)
    config = {
        "name": item[0], "category": item[1], "description": item[0] + " plugin",
        "type": "docker", "image": item[2], "command": item[3],
        "inputs": [{"id": "alvo", "prompt": "Digite o alvo para " + item[0] + ":"}]
    }
    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

print(f"60 PLUGINS CRIADOS NA PASTA {PASTA}!")
