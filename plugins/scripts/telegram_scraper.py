import sys
import urllib.request
import re

if len(sys.argv) < 2:
    print("[!] Erro: Especifique o username do alvo.")
    sys.exit(1)

target = sys.argv[1].replace('@', '').replace('t.me/', '').replace('https://', '')
url = f"https://t.me/{target}"

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})

try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8', errors='ignore')
        
    title = re.search(r'<meta property="og:title" content="(.*?)">', html)
    desc = re.search(r'<meta property="og:description" content="(.*?)">', html)
    img = re.search(r'<meta property="og:image" content="(.*?)">', html)
    
    print(f"=== TELEGRAM OSINT: @{target} ===")
    
    nome = title.group(1) if title else 'Desconhecido / Não Existe'
    if "Telegram: Contact" in nome:
        print("[x] Não foi possível localizar canal ou perfil público válido.")
    else:
        print(f"🔹 Nome/Canal: {nome}")
        print(f"🔹 Biografia (Bio): {desc.group(1) if desc else 'N/A'}")
        print(f"🔹 Link da Foto (URL): {img.group(1) if img else 'N/A'}")

except Exception as e:
    print(f"[-] Erro de conexão com o Telegram web: {e}")
