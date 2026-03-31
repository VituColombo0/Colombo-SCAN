import json
import csv
from fpdf import FPDF
import datetime
import os
import re
import html
from dataclasses import asdict
from core.entities import ScanResult
from core.intelligence import extrair_insights
from core.dorks import generate_dorks

PASTA_RELATORIOS = "relatorios"
os.makedirs(PASTA_RELATORIOS, exist_ok=True)

class PDF(FPDF):
    def header(self):
        # Draw a sleek dark header
        self.set_fill_color(10, 10, 15)
        self.rect(0, 0, 210, 40, 'F')
        
        # Cyberpunk accent line
        self.set_fill_color(0, 210, 255)
        self.rect(0, 38, 210, 2, 'F')

        self.set_xy(12, 12)
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, "COLOMBO SCANNER", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 210, 255)
        self.cell(0, 6, "CONFIDENTIAL // TACTICAL INTELLIGENCE DOSSIER", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(100, 100, 100)
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cell(0, 10, f"SCAN-OSINT-V5 // INTERNAL USE ONLY // GEN_TS: {ts} // PAGE {self.page_no()}", align="C")

def _imprimir_output_pdf(pdf, saida):
    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(30, 30, 30)
    linhas_validas = [l for l in saida.splitlines() if l.strip()]
    linhas_impressas = 0
    for linha in linhas_validas:
        if linhas_impressas > 40: 
            pdf.set_text_color(200, 50, 50)
            pdf.multi_cell(0, 5, txt="\n[--- DATA TRUNCATED FOR READABILITY ---]", new_x="LMARGIN", new_y="NEXT")
            break
        try:
            linha_safe = str(linha).encode('ascii', 'ignore').decode('ascii')
            if len(linha_safe) > 110: linha_safe = linha_safe[:110] + "..."
            if linha_safe.strip():
                pdf.multi_cell(0, 4, txt=linha_safe, new_x="LMARGIN", new_y="NEXT")
                linhas_impressas += 1
        except Exception: pass
    pdf.ln(3)

def _gerar_tabela_entidades(pdf, insights):
    """Gera uma tabela visual das entidades encontradas no PDF."""
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, "RESUMO DE ENTIDADES DESCOBERTAS", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    # Table Header
    pdf.set_fill_color(220, 220, 230)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(40, 8, " TIPO", border=1, fill=True)
    pdf.cell(110, 8, " VALORES (Amostra)", border=1, fill=True)
    pdf.cell(30, 8, " QTD", border=1, fill=True, align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 9)
    by_type = insights.get("by_type", {})
    for tipo, entities in by_type.items():
        vals = [e.value for e in entities]
        unique_vals = list(dict.fromkeys(vals))
        display_text = ", ".join(unique_vals[:4])
        if len(unique_vals) > 4: display_text += f" (+{len(unique_vals)-4})"
        
        # ASCII Safe
        display_text = display_text.encode('ascii', 'ignore').decode('ascii')
        
        pdf.cell(40, 7, f" {tipo.upper()}", border=1)
        pdf.cell(110, 7, f" {display_text}", border=1)
        pdf.cell(30, 7, f" {len(unique_vals)}", border=1, align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

def gerar_relatorio(alvo: str, resultados: list[ScanResult], output_format: str = "html", output_path: str = None) -> str:
    """
    Gera dossiers táticos em múltiplos formatos.
    Prioriza legibilidade e inteligência acionável.
    """
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.ln(10)
    
    # Dossier Info Box
    pdf.set_fill_color(245, 248, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, f" ALVO: {alvo.upper()}", border='TLR', fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    ts_completo = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    pdf.cell(0, 8, f" GERADO EM: {ts_completo} (Local Time)", border='BLR', fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    insights = extrair_insights(resultados)
    
    # KPIs at the top
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 50, 100)
    pdf.cell(60, 10, f"Entidades: {insights['total_unique']}", align='L')
    pdf.cell(60, 10, f"Correlacoes: {insights['total_correlations']}", align='L')
    pdf.cell(60, 10, f"Alertas: {len(insights['alertas'])}", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Entity Table (The "Necessary" stuff)
    if insights.get("total_unique", 0) > 0:
        _gerar_tabela_entidades(pdf, insights)

    # Executive Alerts
    if insights.get("alertas"):
        pdf.set_text_color(180, 0, 0)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 10, "[!] ALERTAS DE ALTO RISCO", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(0, 0, 0)
        for al in insights["alertas"][:10]:
            clean_al = re.sub(r'\[/?[a-z ]+\]', '', str(al))
            clean_al = clean_al.encode('ascii', 'ignore').decode('ascii')
            pdf.multi_cell(0, 5, txt=f" >> {clean_al}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

    # Detailed Findings Header
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(15, 25, 45)
    pdf.cell(0, 12, "DETALHAMENTO POR FERRAMENTA", border='B', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 80, 0)
    pdf.cell(0, 10, "[+] RESULTADOS POSITIVOS", new_x="LMARGIN", new_y="NEXT")
    
    for r in insights.get("positivos", []):
        pdf.set_fill_color(240, 245, 240)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(20, 60, 20)
        pdf.cell(0, 8, f" TOOL: {r.plugin_name}", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        _imprimir_output_pdf(pdf, r.raw_output.strip())

    # Technical Noise at the very end
    if insights.get("ruido"):
        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 10, "[-] VERIFICACOES TECNICAS / RUIDO", border='T', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "I", 8)
        for r in insights.get("ruido", []):
            pdf.cell(0, 5, f" - {r.plugin_name}: Sem novas descobertas relevantes.", new_x="LMARGIN", new_y="NEXT")

    # Caminho Base
    if output_path:
        base_nome = os.path.splitext(os.path.basename(output_path))[0]
        pasta_final = os.path.dirname(output_path) or PASTA_RELATORIOS
    else:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        alvo_safe = re.sub(r'[^a-zA-Z0-9.-]', '_', alvo).strip('_')[:30]
        base_nome = f"colombo_{alvo_safe}_{ts}"
        pasta_final = PASTA_RELATORIOS

    caminho_pdf = os.path.join(pasta_final, f"{base_nome}.pdf")
    caminho_html = os.path.join(pasta_final, f"{base_nome}.html")
    caminho_json = os.path.join(pasta_final, f"{base_nome}.json")
    caminho_csv = os.path.join(pasta_final, f"{base_nome}.csv")

    # Output PDF
    pdf.output(caminho_pdf)

    # JSON & CSV
    with open(caminho_json, 'w', encoding='utf-8') as f_json:
        json.dump([asdict(r) for r in resultados], f_json, indent=4, ensure_ascii=False)

    with open(caminho_csv, 'w', encoding='utf-8', newline='') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["Ferramenta", "Status", "Alvo", "Output RAW"])
        for r in resultados: writer.writerow([r.plugin_name, r.status, r.target, r.raw_output])

    # HTML Luxury Redesign
    html_content = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SCAN DOSSIER - {alvo}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        :root {{ 
            --primary: #00d2ff; 
            --bg: #0a0a0c; 
            --card: #141417; 
            --accent: #ff0055; 
            --text: #e2e8f0;
            --border: rgba(255, 255, 255, 0.08);
        }}
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: 'Inter', sans-serif; 
            background: var(--bg); 
            color: var(--text); 
            margin: 0; 
            padding-bottom: 50px;
            overflow-x: hidden;
        }}
        .hero {{ 
            background: radial-gradient(circle at top right, #1e293b 0%, #0a0a0c 70%); 
            padding: 80px 20px; 
            text-align: left; 
            border-bottom: 1px solid var(--border);
            position: relative;
        }}
        .hero::after {{
            content: ""; position: absolute; bottom: -1px; left: 10%; width: 80%; height: 2px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
        }}
        .container {{ max-width: 1200px; margin: auto; padding: 0 30px; }}
        .kpi-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 25px; 
            margin-top: -50px; 
            position: relative;
            z-index: 10;
        }}
        .glass {{ 
            background: rgba(20, 20, 23, 0.8); 
            backdrop-filter: blur(20px); 
            border: 1px solid var(--border); 
            border-radius: 16px; 
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }}
        .kpi-val {{ font-size: 3em; font-weight: 800; color: #fff; display: block; line-height: 1; }}
        .kpi-label {{ text-transform: uppercase; font-size: 0.75rem; color: var(--primary); letter-spacing: 3px; font-weight: 600; margin-top: 10px; display: block; }}
        
        .section-title {{ 
            font-size: 1.5rem; 
            font-weight: 700; 
            margin: 60px 0 30px; 
            display: flex; 
            align-items: center; 
            color: #fff;
        }}
        .section-title::before {{
            content: ""; width: 4px; height: 1.5rem; background: var(--primary); margin-right: 15px; border-radius: 2px;
        }}

        .card {{ 
            background: var(--card); 
            padding: 25px; 
            margin-bottom: 20px; 
            border-radius: 12px;
            border: 1px solid var(--border);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .card:hover {{ 
            border-color: var(--primary); 
            background: rgba(0, 210, 255, 0.02);
            transform: scale(1.01);
        }}
        
        .badge {{ 
            background: rgba(0, 210, 255, 0.1); 
            color: var(--primary); 
            padding: 6px 14px; 
            border-radius: 8px; 
            font-size: 0.75rem; 
            font-weight: 700; 
            text-transform: uppercase;
        }}
        .tag {{ 
            background: #1e293b; 
            color: #94a3b8; 
            padding: 4px 10px; 
            border-radius: 6px; 
            font-size: 11px; 
            margin: 0 5px 5px 0; 
            display: inline-block; 
            border: 1px solid rgba(255,255,255,0.05);
        }}
        
        pre {{ 
            background: #000; 
            padding: 20px; 
            border-radius: 10px; 
            font-family: 'JetBrains Mono', monospace; 
            color: #10b981; 
            font-size: 13px; 
            overflow-x: auto; 
            border: 1px solid #111; 
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
        }}
        
        .btn-pivot {{ 
            color: #fff; 
            text-decoration: none; 
            font-weight: 600; 
            font-size: 0.85rem; 
            padding: 8px 15px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            margin: 5px;
            display: inline-block;
            transition: all 0.2s;
            border: 1px solid var(--border);
        }}
        .btn-pivot:hover {{ background: var(--primary); color: #000; transform: translateY(-2px); }}
        
        .risk-high {{ border-left: 6px solid var(--accent) !important; }}
        .risk-medium {{ border-left: 6px solid #fbbf24 !important; }}
        
        details summary {{ cursor: pointer; color: #64748b; font-weight: 600; padding: 20px; border-top: 1px solid var(--border); list-style: none; display: flex; align-items: center; justify-content: center; }}
        details summary:hover {{ color: #fff; }}
    </style>
"""
    
    html_content += f"""
<body>
    <div class="hero">
        <div class="container">
            <h1 style="font-size: 3.5rem; margin: 0; font-weight: 800; letter-spacing: -2px;">SCAN <span style="color:var(--primary)">DOSSIER</span></h1>
            <p style="color: #64748b; font-size: 1.1rem; margin-top: 10px; font-family: 'JetBrains Mono', monospace;">
                TARGET_ID: <span style="color: #fff;">{alvo}</span> | 
                STATUS: <span style="color: #10b981;">COMPLETED</span>
            </p>
        </div>
    </div>

    <div class="container">
        <div class="kpi-grid">
            <div class="glass"><span class="kpi-val">{insights['total_unique']}</span><span class="kpi-label">Analyzed Entities</span></div>
            <div class="glass"><span class="kpi-val">{insights['total_correlations']}</span><span class="kpi-label">Correlations</span></div>
            <div class="glass"><span class="kpi-val" style="color: var(--accent);">{len(insights['alertas'])}</span><span class="kpi-label">Intel Alerts</span></div>
        </div>

        <h2 class="section-title">CORRELATED INTELLIGENCE & PIVOTS</h2>
    """
    
    for c in insights["correlacoes"][:15]:
        is_high = c["score"] >= 8
        is_medium = c["score"] >= 4
        risk_class = "risk-high" if is_high else ("risk-medium" if is_medium else "")
        
        html_content += f"""
        <div class="card {risk_class}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                <div>
                    <span class="badge" style="margin-bottom: 8px; display: inline-block;">{c['type'].upper()}</span>
                    <h3 style="margin: 0; font-size: 1.4rem; color: #fff; word-break: break-all;">{html.escape(str(c['value']))}</h3>
                </div>
                <div style="text-align: right;">
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #64748b;">SCORE</span>
                    <div style="font-size: 1.5rem; font-weight: 800; color: { 'var(--accent)' if is_high else 'var(--primary)' }">{c['score']}</div>
                </div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <span style="font-size: 0.7rem; color: #475569; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 8px;">Tactical Sources</span>
                {" ".join([f"<span class='tag'>{t}</span>" for t in c['tools']])}
            </div>
        """
        
        dorks = generate_dorks(c["value"], c["type"])
        if dorks:
            html_content += '<div style="border-top: 1px solid var(--border); padding-top: 15px;">'
            html_content += '<span style="font-size: 0.7rem; color: #475569; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 10px;">Recommended Investigation Pivots</span>'
            for d in dorks:
                html_content += f'<a href="{d["url"]}" target="_blank" class="btn-pivot">⊕ {d["title"]}</a> '
            html_content += '</div>'
        
        html_content += "</div>"
            
    html_content += '<h2 class="section-title">DETAILED DATA STREAM</h2>'
    for r in insights["positivos"]:
        html_content += f"""
        <div class="card" style="border-top: 2px solid #10b981;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h4 style="margin: 0; color: #fff; font-size: 1.1rem; letter-spacing: 1px;">{r.plugin_name.upper()}</h4>
                <span class="tag" style="color: #10b981; border-color: rgba(16, 185, 129, 0.2);">SUCCESS</span>
            </div>
            <pre>{html.escape(str(r.raw_output))}</pre>
        </div>"""
    
    if insights["ruido"]:
        html_content += f"""
        <details>
            <summary>EXPOSE TECHNICAL NOISE & SYSTEM VERIFICATIONS ({len(insights['ruido'])})</summary>
            <div style="padding: 20px;">"""
        for r in insights["ruido"]:
            # Truncate noise for performance
            noise_text = str(r.raw_output)[:500] + ("..." if len(str(r.raw_output)) > 500 else "")
            html_content += f"""
            <div class="card" style="opacity: 0.6; font-size: 0.9rem;">
                <b style="color: #64748b;">{r.plugin_name}</b>
                <pre style="color: #475569; border: none; background: transparent; padding: 10px 0;">{html.escape(noise_text)}</pre>
            </div>"""
        html_content += "</div></details>"
        
    html_content += """
    </div>
    <div style="text-align: center; margin-top: 100px; padding: 40px; border-top: 1px solid var(--border); opacity: 0.3; font-size: 0.8rem; letter-spacing: 2px;">
        COLOMBO SCANNER // END OF TRANSMISSION
    </div>
</body></html>"""
    
    with open(caminho_html, 'w', encoding='utf-8') as f_html:
        f_html.write(html_content)

    mapa_retorno = {
        "pdf": caminho_pdf,
        "html": caminho_html,
        "json": caminho_json,
        "csv": caminho_csv
    }
    return mapa_retorno.get(output_format.lower(), caminho_html)
