import subprocess
import os
import json

ALVOS = {
    "email": "test@example.com",
    "telefone": "+5511988887777",
    "ip": "8.8.8.8",
    "dominio": "scanme.nmap.org",
    "username": "johndoe123"
}

def run_target(tipo, alvo):
    print(f"\n[{tipo.upper()}] Testando alvo: {alvo}")
    # Remove old reports for this target to ensure we check the new one
    base_alvo = "".join(x for x in alvo if x.isalnum())[:20]
    for ext in [".json", ".csv", ".pdf", ".html"]:
        # Naive cleanup, report.py adds timestamp, we will find by looking at dir later
        pass
        
    cmd = ["./.venv/bin/python3", "main.py", "--alvo", alvo, "--seq"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print(f"Status: {proc.returncode}")
        if proc.returncode != 0:
            print(f"Erro:\n{proc.stderr}")
        return proc.stdout
    except subprocess.TimeoutExpired:
        print("Timeout atingido (esperado em ferramentas longas)")
        return "TIMEOUT"

if __name__ == "__main__":
    for tipo, alvo in ALVOS.items():
        out = run_target(tipo, alvo)
        # Check if type was correctly detected in stdout
        if f"Tipo: {tipo}" in out:
            print("✅ Tipo detectado corretamente.")
        else:
            print(f"❌ Falha na detecção de tipo para {alvo}. Saída parcial:")
            print("\n".join(out.splitlines()[:10]))
        
        # Check summary
        summary_lines = [l for l in out.splitlines() if "Entidades" in l or "Correla" in l]
        if summary_lines:
            print(f"Inteligência gerada: {summary_lines}")
        else:
            print("⚠️ Sem sumário de inteligência na saída.")
