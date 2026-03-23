import sys
import re
import urllib.request
from urllib.parse import quote

# Este script simula o comportamento de um 'Dorker' que busca documentos no dominio
# e tenta ler os metadados brutos usando comandos do sistema.

if len(sys.argv) < 2:
    print("[!] Erro: Especifique o dominio alvo.")
    sys.exit(1)

domain = sys.argv[1]
print(f"=== BUSCA RECURSIVA DE DOCUMENTOS: {domain} ===")

# Simulando busca por PDFs publicos no index (Google Dork mimic)
# Nota: Em um ambiente Docker real, poderiamos usar ferramentas de dorking pesado.
# Aqui, simularemos a descoberta para que o ExifTool (docker) processe.

print(f"[*] Escaneando diretórios públicos de {domain} em busca de .pdf, .docx, .xlsx...")
print("[+] Buscando metadados de autoria e versões de software via ExifTool...")

# Exemplo de comando que seria enviado para o runner
# O runner pode rodar: docker run exiftool http://site.com/doc.pdf
print(f"[TIP] Use o 'Modo Manual > Documentos' para processar URLs específicas encontradas.")
