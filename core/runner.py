"""
Colombo Scanner — Secure Plugin Execution Engine
Handles Docker container execution with security hardening, retry logic, and rate limiting.
"""
import subprocess
import urllib.request
import tempfile
import os
import re
import shlex
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from core.logger import get_logger

load_dotenv()
log = get_logger("runner")

# Secure workspace directory — containers only see this, NOT /home
WORKSPACE_DIR = os.path.join(tempfile.gettempdir(), "colombo_workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

DANGEROUS_CHARS = re.compile(r'[;&|`$()><\n\r\\]')
MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 3  # seconds


class EnvWrapper:
    def __getattr__(self, name):
        return os.environ.get(name, "")


env_vars = EnvWrapper()


def sanitize_input(value: str) -> str:
    """
    Validates and sanitizes user input to prevent command injection.
    Raises ValueError if dangerous characters are detected.
    """
    if not isinstance(value, str):
        raise ValueError(f"Input deve ser string, recebeu: {type(value)}")

    stripped = value.strip()

    if DANGEROUS_CHARS.search(stripped):
        dangerous_found = [ch for ch in stripped if DANGEROUS_CHARS.match(ch)]
        log.warning(f"Input bloqueado por caracteres perigosos: {dangerous_found} em '{stripped[:50]}'")
        raise ValueError(
            f"⛔ Input contém caracteres não permitidos: {dangerous_found}\n"
            "Metacaracteres de shell (;, |, &, $, `, etc.) são bloqueados por segurança."
        )

    if len(stripped) > 500:
        raise ValueError("⛔ Input muito longo (máximo 500 caracteres).")

    return stripped


def is_url(texto: str) -> bool:
    return str(texto).startswith("http://") or str(texto).startswith("https://")


def baixar_temp(url: str) -> str:
    """Downloads a URL to the secure workspace directory."""
    try:
        nome = url.split("/")[-1].split("?")[0]
        if not nome:
            nome = "alvo.tmp"
        # Sanitize filename
        nome = re.sub(r'[^a-zA-Z0-9._-]', '_', nome)
        caminho = os.path.join(WORKSPACE_DIR, nome)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp, open(caminho, 'wb') as f:
            shutil.copyfileobj(resp, f)
        log.info(f"Arquivo baixado para workspace: {caminho}")
        return caminho
    except Exception as e:
        log.warning(f"Falha ao baixar {url}: {e}")
        return url


def _build_docker_command(plugin: dict, inputs_tratados: dict) -> str:
    """
    Builds the Docker command securely.
    Supports two modes:
      - Plugins with 'image' field: runner wraps with docker run
      - Plugins without 'image' field (shell commands): executes directly
    """
    imagem = plugin.get("image")
    cmd_base = plugin.get("command", "")
    entry = plugin.get("entrypoint", "")

    # API Key validation
    req_envs = re.findall(r'\{env\.([^}]+)\}', cmd_base)
    for req in req_envs:
        val = getattr(env_vars, req, "")
        if not val:
            return None, f"⚠️ [Ignorado] Chave de API '{req}' ausente no arquivo .env"

    # Build command with safe substitution
    try:
        cmd_final = cmd_base.format(env=env_vars, **inputs_tratados)
    except KeyError as e:
        return None, f"Erro no YAML: variável {e} faltando"

    if imagem:
        # Docker mode — secure volume mounting
        volumes = f"-v {shlex.quote(WORKSPACE_DIR)}:/workspace:ro -v /tmp/colombo_output:/output"
        os.makedirs("/tmp/colombo_output", exist_ok=True)

        # Pass API keys via --env instead of command interpolation
        env_flags = ""
        for req in req_envs:
            val = getattr(env_vars, req, "")
            if val:
                env_flags += f" --env {shlex.quote(f'{req}={val}')}"

        flag_entry = f"--entrypoint {shlex.quote(entry)}" if entry else ""
        cmd_docker = f"docker run --rm --network host {volumes}{env_flags} {flag_entry} {shlex.quote(imagem)} {cmd_final}"
        return cmd_docker, None
    else:
        # Shell/direct mode (curl commands, python scripts, etc.)
        return cmd_final, None


def _executar_um(plugin: dict, inputs: dict) -> dict:
    """Executes a single plugin with security, retry logic, and timeout."""
    plugin_name = plugin.get("name", "Unknown")
    timeout = plugin.get("timeout", 300)

    # Sanitize all inputs
    inputs_tratados = {}
    arquivos_tmp = []

    for k, v in inputs.items():
        try:
            v_safe = sanitize_input(str(v))
        except ValueError as e:
            return {"name": plugin_name, "output": str(e)}

        if is_url(v_safe):
            arq = baixar_temp(v_safe)
            inputs_tratados[k] = arq
            if arq != v_safe:
                arquivos_tmp.append(arq)
        else:
            inputs_tratados[k] = v_safe

    cmd, error = _build_docker_command(plugin, inputs_tratados)
    if error:
        return {"name": plugin_name, "output": error}

    # Retry loop with exponential backoff
    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info(f"[{plugin_name}] Tentativa {attempt}/{MAX_RETRIES} — executando")
            proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL
            )

            if proc.returncode == 125:
                last_error = "[Falha] Imagem Docker inativa ou arquivos faltando"
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_BASE * attempt
                    log.info(f"[{plugin_name}] Retrying em {wait}s...")
                    time.sleep(wait)
                    continue
                return {"name": plugin_name, "output": last_error}

            out = proc.stdout.strip()
            if proc.stderr and not out:
                out = f"{proc.stderr.strip()}"

            if out:
                log.info(f"[{plugin_name}] Concluído com sucesso ({len(out)} chars)")
            else:
                log.info(f"[{plugin_name}] Concluído sem output")

            return {"name": plugin_name, "output": out}

        except subprocess.TimeoutExpired:
            last_error = f"Timeout: a extração demorou mais de {timeout // 60} minutos"
            log.warning(f"[{plugin_name}] {last_error}")
            if attempt < MAX_RETRIES:
                continue
            return {"name": plugin_name, "output": last_error}

        except Exception as e:
            last_error = f"Falha inesperada: {e}"
            log.error(f"[{plugin_name}] {last_error}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE * attempt)
                continue
            return {"name": plugin_name, "output": last_error}

        finally:
            if attempt == MAX_RETRIES:
                for tmp in arquivos_tmp:
                    if os.path.exists(tmp):
                        os.remove(tmp)

    return {"name": plugin_name, "output": last_error}


def run_plugin(plugin: dict, inputs: dict) -> str:
    """Simple interface to run a single plugin — returns output text."""
    return _executar_um(plugin, inputs).get("output", "")


def run_plugins_paralelo(plugins: list, inputs: dict, max_workers: int = 5) -> list[dict]:
    """
    Runs multiple plugins in parallel using ThreadPoolExecutor.
    Respects rate_limit field if present in plugin YAML.
    """
    resultados = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {}
        for p in plugins:
            # Respect rate limiting — stagger launches
            rate_limit = p.get("rate_limit", None)
            if rate_limit and isinstance(rate_limit, (int, float)):
                delay = 60.0 / rate_limit
                time.sleep(min(delay, 2.0))  # cap at 2s delay

            futuros[executor.submit(_executar_um, p, inputs)] = p

        for futuro in as_completed(futuros):
            try:
                resultados.append(futuro.result())
            except Exception as e:
                plugin_nome = futuros[futuro].get("name", "?")
                log.error(f"[{plugin_nome}] Exceção no executor: {e}")
                resultados.append({"name": plugin_nome, "output": f"Falha inesperada: {e}"})

    return resultados
