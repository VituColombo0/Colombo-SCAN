import urllib.request
import json
import threading
import time
import subprocess

API_URL = "http://127.0.0.1:8000"

def start_server():
    print("[INIT] Iniciando servidor API...")
    return subprocess.Popen(["./.venv/bin/python3", "main.py", "--api"])

def send_scan(target, i):
    payload = {"target": target, "max_workers": 2}
    print(f"[REQ {i}] Enviando scan para {target}...")
    try:
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": "colombo_secret_key_v4"
        }
        req = urllib.request.Request(f"{API_URL}/scan", data=data, 
                                     headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode())
            print(f"[RES {i}] Status: {resp.status} | Scan ID: {res_data.get('scan_id')}")
    except Exception as e:
        print(f"[ERR {i}] Falha na requisição: {e}")

if __name__ == "__main__":
    server_proc = start_server()
    time.sleep(5) # Wait for startup
    
    targets = ["google.com", "bing.com", "duckduckgo.com", "yahoo.com", "brave.com"]
    threads = []
    
    for i, t in enumerate(targets):
        th = threading.Thread(target=send_scan, args=(t, i))
        th.start()
        threads.append(th)
        
    for th in threads:
        th.join()
    
    print("\n[INFO] Aguardando para processamento (verifique logs)...")
    time.sleep(10)
    
    print("[INFO] Encerrando servidor.")
    server_proc.terminate()
