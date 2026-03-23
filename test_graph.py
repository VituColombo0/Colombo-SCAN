from core.graph import gerar_grafo
import os

dummy_results = [
    {"name": "Dork Engine", "output": "marcos@empresa.com.br"},
    {"name": "Nmap Scan", "output": "IP do sv: 192.168.1.10"},
    {"name": "URL Finder", "output": "Acesso via https://admin.empresa.com.br/login"},
    {"name": "Sherlock", "output": "User on Twitter: @marcos_oficial"},
    {"name": "PhoneHunter", "output": "Contato: 11988887777"}
]

caminho = gerar_grafo("empresa.com.br", dummy_results)
print(f"Grafo gerado em: {caminho}")
