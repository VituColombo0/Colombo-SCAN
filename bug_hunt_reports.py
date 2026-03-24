import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.report import gerar_relatorio

def test_massive_report():
    alvo = "stress_test_target"
    # Create a massive output (10,000 lines of gibberish)
    massive_output = "\n".join([f"Line {i}: " + "X" * 100 for i in range(10000)])
    
    resultados = [
        {"name": "MassiveTool_1", "output": massive_output},
        {"name": "MassiveTool_2", "output": "Short output"},
        {"name": "Malicious_HTML", "output": "<script>alert('XSS')</script> & <div style='color:red'>Test</div>"}
    ]
    
    print("[TESTE] Gerando relatório massivo...")
    try:
        pdf_path = gerar_relatorio(alvo, resultados)
        print(f"✅ Sucesso! PDF gerado em: {pdf_path}")
        
        base = pdf_path.replace(".pdf", "")
        for ext in [".json", ".csv"]:
            if os.path.exists(base + ext):
                size = os.path.getsize(base + ext)
                print(f"📦 Arquivo {ext} gerado: {size} bytes")
            else:
                print(f"❌ Falha ao gerar {ext}")
                
    except Exception as e:
        print(f"❌ Erro catastrófico na geração: {e}")

if __name__ == "__main__":
    test_massive_report()
