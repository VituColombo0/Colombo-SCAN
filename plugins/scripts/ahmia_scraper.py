import sys
import urllib.request
from urllib.parse import quote

if len(sys.argv) < 2:
    print("[!] Erro: Especifique o alvo (email, nome ou dominio) para busca na Dark Web.")
    sys.exit(1)

target = quote(sys.argv[1])
url = f"https://ahmia.fi/search/?q={target}"

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8', errors='ignore')
    
    import re
    results = re.findall(r'<li class="result">.*?<h4><a href="(.*?)">(.*?)</a></h4>.*?<p>(.*?)</p>', html, re.S)
    
    print(f"=== AHMIA DARK WEB SEARCH: {sys.argv[1]} ===")
    if not results:
        print("[x] Nenhum resultado público encontrado no índice Ahmia.")
    else:
        limit = 10
        count = 0
        for link, title, snippet in results:
            if count >= limit:
                break
            print(f"\n🔗 Onion: {link}")
            print(f"📌 Titulo: {title.strip()}")
            clean_snippet = re.sub('<[^<]+?>', '', snippet).strip()
            print(f"📝 Trecho: {clean_snippet[:200]}...")
            count += 1

except Exception as e:
    print(f"[-] Erro ao acessar Ahmia: {e}")
