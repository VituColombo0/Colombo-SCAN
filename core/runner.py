"""
Colombo_SCAN — Secure Plugin Execution Engine
Handles Docker container execution with security hardening, retry logic, and rate limiting.
"""
import subprocess
import os
import re
import time
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from rich.console import Console
from core.logger import get_logger
from core.entities import ScanResult
from core.database import check_cache_result
from core.auth_manager import get_auth_env

load_dotenv()
log = get_logger("runner")
console = Console()

WORKSPACE_DIR = os.path.join(tempfile.gettempdir(), "colombo_workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 3

class EnvWrapper:
    def __getattr__(self, name):
        import shlex
        return shlex.quote(os.environ.get(name, ""))

env_vars = EnvWrapper()

def sanitize_input(value: str) -> str:
    """
    Blocks lethal shell meta-characters and directory traversal attempts.
    """
    if not isinstance(value, str):
        raise ValueError(f"Input deve ser string, recebeu: {type(value)}")
    
    stripped = value.strip()
    if not stripped:
        return ""
        
    if len(stripped) > 250: # Reduced from 500 for tighter security
        raise ValueError("⛔ Input excessivamente longo.")

    if stripped.startswith("-"):
        log.warning(f"Tentativa de Argument Injection: {stripped}")
        raise ValueError("⛔ Input inválido (não pode iniciar com hífen).")

    # Forbidden shell metacharacters
    # We allow & only inside URLs (http/https) since it's used as query separator
    is_url = stripped.lower().startswith("http://") or stripped.lower().startswith("https://")
    if is_url:
        full_dangerous = re.compile(r'[;|`$()><\n\r\\\\]')
    else:
        full_dangerous = re.compile(r'[;&|`$()><\n\r\\\\]')
    if full_dangerous.search(stripped):
        log.warning(f"Sanitização bloqueou entrada suspeita: {stripped[:30]}...")
        raise ValueError("⛔ Caracteres perigosos detectados no alvo.")
        
    if ".." in stripped:
        log.warning(f"Tentativa de Directory Traversal: {stripped}")
        raise ValueError("⛔ Caminho inválido (traversal detectado).")

    return stripped

def _build_docker_command(plugin: dict, inputs: dict):
    imagem = plugin.get("image")
    cmd_base = plugin.get("command", "")
    entry = plugin.get("entrypoint", "")
    
    import shlex
    inputs_cotados = {k: shlex.quote(str(v)) for k, v in inputs.items()}
    try:
        cmd_final = cmd_base.format(env=env_vars, **inputs_cotados)
    except KeyError as e:
        return None, f"Erro no YAML: {e}"

    if imagem:
        # SECURITY: Using bridge network instead of host for isolation.
        # Adding --cap-drop=ALL and --security-opt to harden the container.
        volumes = f"-v {shlex.quote(WORKSPACE_DIR)}:/workspace:ro"
        flag_entry = f"--entrypoint {shlex.quote(entry)}" if entry else ""
        
        cmd_docker = (
            f"docker run --rm --network bridge "
            f"--cap-drop=ALL --security-opt=no-new-privileges "
            f"{volumes} {flag_entry} {shlex.quote(imagem)} {cmd_final}"
        )
        return cmd_docker, None
    return cmd_final, None

def _executar_um(plugin: dict, inputs: dict) -> ScanResult:
    plugin_name = plugin.get("name", "Unknown")
    timeout = plugin.get("timeout", 300)
    alvo = inputs.get("alvo", "unknown")
    start_time = time.time()

    cached = check_cache_result(plugin_name, alvo, hours=24)
    if cached:
        log.info(f"[CACHE HIT] {plugin_name} para {alvo}")
        return ScanResult(
            plugin_name=plugin_name,
            target=alvo,
            raw_output=cached["output"],
            status="success (cached)",
            execution_time=0.0,
            layer=inputs.get("camada", 1)
        )

    try:
        inputs_tratados = {k: sanitize_input(str(v)) for k, v in inputs.items()}
    except ValueError as e:
        return ScanResult(plugin_name=plugin_name, target=alvo, raw_output=str(e), status="error")

    cmd, error = _build_docker_command(plugin, inputs_tratados)
    if error:
        return ScanResult(plugin_name=plugin_name, target=alvo, raw_output=error, status="skipped")

    # Shadow Auth Injection
    env_merged = os.environ.copy()
    for auth_k, auth_v in get_auth_env().items():
        env_merged[auth_k.upper()] = str(auth_v)

    last_output = ""
    status = "error"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            proc = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                timeout=timeout, 
                text=True, 
                errors='replace',
                env=env_merged
            )
            last_output = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode == 0:
                status = "success"
                break
        except Exception as e:
            last_output = str(e)
            status = "error"
            if attempt < MAX_RETRIES: time.sleep(RETRY_BACKOFF_BASE * attempt)

    return ScanResult(
        plugin_name=plugin_name,
        target=alvo,
        raw_output=last_output.strip(),
        status=status,
        execution_time=time.time() - start_time,
        layer=inputs.get("camada", 1)
    )

def run_plugins_paralelo(plugins: list, inputs: dict, max_workers: int = 5) -> list[ScanResult]:
    resultados = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {executor.submit(_executar_um, p, inputs): p for p in plugins}
        for futuro in as_completed(futuros):
            try:
                resultados.append(futuro.result())
            except Exception as e:
                log.error(f"Erro no executor: {e}")
    return resultados

def run_plugin(plugin: dict, inputs: dict) -> str:
    res = _executar_um(plugin, inputs)
    return res.raw_output
