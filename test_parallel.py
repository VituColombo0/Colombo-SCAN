import subprocess
import os

def run_workflow(alvo):
    print(f"\n[WORKFLOW] Iniciando 2 camadas para: {alvo}")
    # Simulating the interactive choice or just using silent mode with specific cat
    # Since silent mode doesn't support recursive workflow yet (it runs modo_silencioso), 
    # I will call a small wrapper to test the core directly.
    
    # Actually, main.py only runs workflow in interactive mode.
    # I'll create a small script to test core/workflow.py directly.
    pass

def run_parallel(alvo):
    print(f"\n[PARALELO] Testando alvo: {alvo}")
    cmd = ["./.venv/bin/python3", "main.py", "--alvo", alvo] # No --seq = parallel
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Status: {proc.returncode}")
    print(f"Saída:\n{proc.stdout[-1000:]}") # Last 1000 chars

if __name__ == "__main__":
    run_parallel("test@example.com")
