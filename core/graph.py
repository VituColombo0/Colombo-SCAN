import os
import json
import re
import datetime
import html

PASTA_RELATORIOS = "relatorios"
os.makedirs(PASTA_RELATORIOS, exist_ok=True)

from core.entities import ScanResult

def _extrair_nos_arestas(alvo: str, resultados: list[ScanResult]) -> tuple[list, list]:
    """
    parse basico nos resultados pra achar emails, IPs, usuarios e URLs
    e montar os nos e arestas do grafo
    """
    nos = [{"id": 0, "label": alvo, "color": "#e74c3c", "size": 30}]
    arestas = []
    id_no = 1
    vistos = set()
    PADROES = {
        "email":    r'[\w.+-]+@[\w-]+\.[a-z]{2,}',
        "url":      r'https?://[^\s"\'<>]+',
        "ip":       r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        "usuario":  r'@([\w._]{3,30})',
        "telefone": r'\+?\d[\d\s\-\(\)]{7,16}\d',
    }

    CORES = {
        "email": "#3498db", "url": "#2ecc71",
        "ip": "#f39c12", "usuario": "#9b59b6", "telefone": "#1abc9c"
    }

    for res in resultados:
        texto = res.raw_output
        ferramenta = res.plugin_name

        for tipo, padrao in PADROES.items():
            for match in re.findall(padrao, texto, re.IGNORECASE):
                val = match.strip()
                if val == alvo or val in vistos or len(val) > 100:
                    continue
                vistos.add(val)

                val_escaped = html.escape(val[:40])
                ferramenta_escaped = html.escape(ferramenta[:20])

                nos.append({
                    "id": id_no,
                    "label": val_escaped,
                    "title": f"Encontrado por: {ferramenta_escaped}",
                    "group": tipo,
                    "value": 15
                })
                arestas.append({"from": 0, "to": id_no, "label": ferramenta_escaped})
                id_no += 1

    return nos, arestas

def gerar_grafo(alvo: str, resultados: list[ScanResult]) -> str:
    """gera um html interativo com o grafo de relacionamentos do alvo"""
    nos, arestas = _extrair_nos_arestas(alvo, resultados)
    template_path = os.path.join(os.path.dirname(__file__), "graph_template.html")
    # ... rest of the function remains same ...
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    html = template.replace("{alvo}", html.escape(alvo)) \
                   .replace("{nodes}", json.dumps(nos)) \
                   .replace("{edges}", json.dumps(arestas))

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize TARGET to prevent Path Traversal
    alvo_safe = re.sub(r'[^a-zA-Z0-9.-]', '_', alvo).strip('_')[:30]
    nome = f"colombo_grafo_{alvo_safe}_{ts}.html"
    caminho = os.path.join(PASTA_RELATORIOS, nome)

    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(html)

    return caminho
