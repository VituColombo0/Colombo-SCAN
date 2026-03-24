import subprocess
import os
import sys

ALVOS = {
    "email": "test@example.com",
    "dominio": "scanme.nmap.org"
}

def run_target(tipo, alvo):
    print(f"\n[{tipo.upper()}] Testando alvo: {alvo}")
    cmd = ["./.venv/bin/python3", "main.py", "--alvo", alvo, "--seq"]
    
    # We use Popen to see output line by line if possible, 
    # but here we just want to ensure it doesn't hang forever
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            print(f"  {line.strip()}")
        proc.wait(timeout=180)
        print(f"Status: {proc.returncode}")
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        print("Timeout atingido!")
        proc.kill()
        return False

if __name__ == "__main__":
    for tipo, alvo in ALVOS.items():
        run_target(tipo, alvo)
    print("\n[FIM] Testes concluídos.")
