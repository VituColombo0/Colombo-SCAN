import subprocess
import sys
from rich.console import Console

console = Console()

def check_dependencies():
    """
    Realiza o Pre-Flight Health Check para garantir que os binários fundamentais 
    do sistema estão presentes antes de iniciar a varredura paralela massiva.
    """
    faltantes = []
    
    # Check Docker
    try:
        resultado = subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if resultado.returncode != 0:
            console.print("[red][!][/red] Docker não está rodando ou você não tem permissão.")
            faltantes.append("docker-daemon")
    except FileNotFoundError:
        console.print("[red][!][/red] Binário do 'docker' não encontrado no sistema.")
        faltantes.append("docker")

    # Check curl (usado por muitos plugins web)
    try:
        subprocess.run(["curl", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        faltantes.append("curl")

    # Check jq (usado para parsear saídas JSON em bash)
    try:
        subprocess.run(["jq", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        faltantes.append("jq")

    if faltantes:
        console.print(f"\n[bold red]Dependências críticas ausentes: {', '.join(faltantes)}[/bold red]")
        console.print("Por favor, instale ou ative esses serviços antes de iniciar o Colombo Scanner.")
        sys.exit(1)
