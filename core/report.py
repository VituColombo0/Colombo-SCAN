import json
import csv
from fpdf import FPDF
import datetime
import os
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

def gerar_relatorio(alvo: str, resultados: list[dict]) -> str:
    """
    recebe o alvo investigado e uma lista de dicts com
    {"name": nome_da_ferramenta, "output": saida}
    e gera um pdf formatado na pasta relatorios/
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
        nome = r.get("name", "Ferramenta")
        saida = r.get("output", "").strip()
        pdf.set_fill_color(240, 240, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 30, 120)
        pdf.cell(0, 8, f"=== {nome} ===", fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(30, 30, 30)
        for linha in saida.splitlines():
            try:
                pdf.multi_cell(0, 5, txt=linha[:300])
            except Exception:
                pass
        pdf.ln(4)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_nome = f"colombo_{alvo.replace(' ', '_')[:30]}_{ts}"
    caminho_pdf = os.path.join(PASTA_RELATORIOS, f"{base_nome}.pdf")
    pdf.output(caminho_pdf)

    caminho_json = os.path.join(PASTA_RELATORIOS, f"{base_nome}.json")
    with open(caminho_json, 'w', encoding='utf-8') as f_json:
        json.dump(resultados, f_json, indent=4, ensure_ascii=False)

    caminho_csv = os.path.join(PASTA_RELATORIOS, f"{base_nome}.csv")
    with open(caminho_csv, 'w', encoding='utf-8', newline='') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["Ferramenta", "Output RAW"])
        for r in resultados:
            writer.writerow([r.get("name", "N/A"), r.get("output", "")])

    return caminho_pdf
