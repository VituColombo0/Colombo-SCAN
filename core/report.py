import json
import csv
from fpdf import FPDF
import datetime
import os
import re
from dataclasses import asdict
from core.entities import ScanResult

PASTA_RELATORIOS = "relatorios"
os.makedirs(PASTA_RELATORIOS, exist_ok=True)

class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_fill_color(20, 20, 40)
        self.set_text_color(0, 200, 230)
        self.cell(0, 12, "COLOMBO SCANNER - Relatório Forense OSINT", align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f"Colombo Scanner | {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} | Pag. {self.page_no()}", align="C")

def gerar_relatorio(alvo: str, resultados: list[ScanResult]) -> str:
    """
    recebe o alvo investigado e uma lista de objetos ScanResult
    e gera um pdf, json e csv na pasta relatorios/
    """
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 8, f"Alvo Investigado: {alvo}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"Data: {datetime.datetime.now().strftime('%d/%m/%Y as %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    for r in resultados:
        nome = r.plugin_name
        saida = r.raw_output.strip()
        pdf.set_fill_color(240, 240, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 30, 120)
        pdf.cell(0, 8, f"=== {nome} ===", fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(30, 30, 30)
        linhas_validas = [l for l in saida.splitlines() if l.strip()]
        linhas_impressas = 0
        
        for linha in linhas_validas:
            if linhas_impressas > 100:
                pdf.set_text_color(200, 50, 50)
                pdf.multi_cell(0, 5, txt=f"\n... ✂️ [Saída truncada no PDF] ✂️ ...")
                break
            try:
                if len(linha) > 120:
                    linha = linha[:120] + "..."
                pdf.multi_cell(0, 5, txt=linha)
                linhas_impressas += 1
            except Exception:
                pass
        pdf.ln(4)
    
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    alvo_safe = re.sub(r'[^a-zA-Z0-9.-]', '_', alvo).strip('_')[:30]
    base_nome = f"colombo_{alvo_safe}_{ts}"
    caminho_pdf = os.path.join(PASTA_RELATORIOS, f"{base_nome}.pdf")
    pdf.output(caminho_pdf)

    # JSON export with dict conversion
    caminho_json = os.path.join(PASTA_RELATORIOS, f"{base_nome}.json")
    with open(caminho_json, 'w', encoding='utf-8') as f_json:
        json.dump([asdict(r) for r in resultados], f_json, indent=4, ensure_ascii=False)

    # CSV export
    caminho_csv = os.path.join(PASTA_RELATORIOS, f"{base_nome}.csv")
    with open(caminho_csv, 'w', encoding='utf-8', newline='') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["Ferramenta", "Status", "Alvo", "Output RAW"])
        for r in resultados:
            writer.writerow([r.plugin_name, r.status, r.target, r.raw_output])

    return caminho_pdf
