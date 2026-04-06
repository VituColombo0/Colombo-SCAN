import sys
import os
sys.path.insert(0, '/home/lirool/Área de trabalho/Colombo_SCAN')

from core.engine import ColomboEngine
from core.report import gerar_relatorio
from core.entities import ScanResult
from core.dorks import generate_dorks
from core.entities import EntityType
import time
import json

engine = ColomboEngine()

# Expert OSINT Constraints
nome = "Victor Colombo"
partial_phone = "35999"  # DDD 35, Mobile 9, prefix 99

print(f"[+] Iniciando Investigação Pericial: {nome} + {partial_phone}******")

# 1. Custom Google Dorks Cross-Match
custom_dorks = [
    {"title": "Cross-match LinkedIn + DDD", "query": f'site:linkedin.com/in "{nome}" "{partial_phone}"'},
    {"title": "Cross-match Escavador/JusBrasil", "query": f'"{nome}" "{partial_phone}" (site:jusbrasil.com.br OR site:escavador.com)'},
    {"title": "Vazamentos / Pastebin", "query": f'site:pastebin.com "{nome}" "{partial_phone}"'},
    {"title": "Busca Aberta", "query": f'"{nome}" "{partial_phone}"'}
]

# We will create fake ScanResults from the custom dorks so they appear in the report
resultados = []

dorks_output = []
for d in custom_dorks:
    url = f"https://www.google.com/search?q={d['query'].replace(' ', '+')}"
    dorks_output.append(f"🔍 {d['title']}: {url}")

resultados.append(
    ScanResult(
        plugin_name="Expert_Dork_Correlation",
        target="Victor Colombo 35999",
        raw_output="\\n".join(dorks_output),
        layer=1,
        status="completed"
    )
)

print("[+] Dorks criadas. Executando plugins focados em NOME...")

# 2. Run selected plugins for the name to see what we find (with strict timeouts)
# We will filter out heavy/slow plugins to get a fast, functional result.
fast_plugins = [
    p for p in engine.plugins 
    if p["name"] in [
        "Google Dorking Engine", 
        "Real-time Social Trends (Social Searcher)", 
        "Telegram Basic OSINT (Native Scraper)"
    ]
]

print(f"[+] Plugins selecionados: {[p['name'] for p in fast_plugins]}")
from core.runner import run_plugins_paralelo

res_nome = run_plugins_paralelo(fast_plugins, {"alvo": nome})
for r in res_nome:
    resultados.append(r)
    print(f"  - {r.plugin_name}: {len(r.raw_output)} bytes retornados. Status: {r.status}")

# 3. Compile the report
alvo_final = f"Victor Colombo (Tel: {partial_phone}******)"
print(f"[+] Gerando Relatório PDF para {alvo_final}...")

try:
    report_path = gerar_relatorio(alvo_final, resultados, output_format="pdf", output_path="relatorios/Pericia_VictorColombo.pdf")
    print(f"[✓] Sucesso! PDF gerado em: {report_path}")
except Exception as e:
    print(f"[X] Erro ao gerar PDF: {e}")
