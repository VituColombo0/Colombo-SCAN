"""
Colombo Scanner — Pre-Flight Health Check (Non-Blocking)
Checks for required system dependencies but does NOT block the application.
Returns status dict for the UI to display.
"""
import subprocess
from core.logger import get_logger

log = get_logger("health_check")


def check_dependencies() -> dict:
    """
    Checks for Docker, curl, and jq.
    Returns a dict with status of each dependency.
    Does NOT call sys.exit() — the application continues even if deps are missing.
    """
    status = {
        "docker": {"ok": False, "msg": ""},
        "curl": {"ok": False, "msg": ""},
        "jq": {"ok": False, "msg": ""},
    }

    # Check Docker
    try:
        resultado = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        if resultado.returncode == 0:
            status["docker"] = {"ok": True, "msg": "Operacional"}
        else:
            msg = "Docker não está rodando ou sem permissão"
            status["docker"] = {"ok": False, "msg": msg}
            log.warning(msg)
    except FileNotFoundError:
        msg = "Binário 'docker' não encontrado no sistema"
        status["docker"] = {"ok": False, "msg": msg}
        log.warning(msg)
    except subprocess.TimeoutExpired:
        msg = "Docker info timeout — daemon pode estar travado"
        status["docker"] = {"ok": False, "msg": msg}
        log.warning(msg)

    # Check curl
    try:
        subprocess.run(["curl", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        status["curl"] = {"ok": True, "msg": "Operacional"}
    except FileNotFoundError:
        status["curl"] = {"ok": False, "msg": "Binário 'curl' não encontrado"}
        log.warning("curl não encontrado")
    except subprocess.TimeoutExpired:
        status["curl"] = {"ok": False, "msg": "curl timeout"}

    # Check jq
    try:
        subprocess.run(["jq", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        status["jq"] = {"ok": True, "msg": "Operacional"}
    except FileNotFoundError:
        status["jq"] = {"ok": False, "msg": "Binário 'jq' não encontrado"}
        log.warning("jq não encontrado")
    except subprocess.TimeoutExpired:
        status["jq"] = {"ok": False, "msg": "jq timeout"}

    return status


def format_status_for_banner(status: dict) -> str:
    """Returns a Rich-formatted string for the banner status display."""
    docker_status = status.get("docker", {})
    if docker_status.get("ok"):
        return "[bold green]● Connected[/bold green]"
    else:
        return f"[bold red]● Offline[/bold red] [dim]({docker_status.get('msg', '?')})[/dim]"
