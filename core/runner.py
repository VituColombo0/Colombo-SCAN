import subprocess
import urllib.request
import tempfile
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

class EnvWrapper:
    def __getattr__(self, name):
        return os.environ.get(name, "")

env_vars = EnvWrapper()

def is_url(texto: str) -> bool:
    return str(texto).startswith("http://") or str(texto).startswith("https://")

def baixar_temp(url: str) -> str:
    try:
        tmp_dir = tempfile.gettempdir()
        nome = url.split("/")[-1].split("?")[0]
        if not nome:
            nome = "alvo.tmp"
        caminho = os.path.join(tmp_dir, nome)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp, open(caminho, 'wb') as f:
            shutil.copyfileobj(resp, f)
        return caminho
    except Exception:
        return url

def _executar_um(plugin: dict, inputs: dict) -> dict:
    """executa um unico plugin e retorna o resultado em dict - usado pelo executor paralelo"""
    imagem = plugin.get("image")
    cmd_base = plugin.get("command", "")
    entry = plugin.get("entrypoint", "")

    inputs_tratados = {}
    arquivos_tmp = []

    for k, v in inputs.items():
        if is_url(v):
            arq = baixar_temp(v)
            inputs_tratados[k] = arq
            if arq != v:
                arquivos_tmp.append(arq)
        else:
            inputs_tratados[k] = v

    try:
        cmd_final = cmd_base.format(env=env_vars, **inputs_tratados)
    except KeyError as e:
        return {"name": plugin.get("name"), "output": f"erro no yaml: variavel {e} faltando"}

    volumes = "-v /home:/home -v /tmp:/tmp"
    flag_entry = f"--entrypoint {entry}" if entry else ""
    cmd_docker = f"docker run --rm {volumes} {flag_entry} {imagem} {cmd_final}"

    try:
        proc = subprocess.run(cmd_docker, shell=True, capture_output=True, text=True, timeout=120)
        out = proc.stdout
        if proc.stderr:
            out += f"\n[stderr]:\n{proc.stderr}"
        return {"name": plugin.get("name"), "output": out.strip()}
    except subprocess.TimeoutExpired:
        return {"name": plugin.get("name"), "output": "timeout: o plugin demorou mais de 2 minutos"}
    except Exception as e:
        return {"name": plugin.get("name"), "output": f"falha ao subir {imagem}: {e}"}
    finally:
        for tmp in arquivos_tmp:
            if os.path.exists(tmp):
                os.remove(tmp)

def run_plugin(plugin: dict, inputs: dict) -> str:
    """interface simples para rodar um plugin e retornar apenas o texto (compatibilidade)"""
    return _executar_um(plugin, inputs).get("output", "")

def run_plugins_paralelo(plugins: list, inputs: dict, max_workers: int = 5) -> list[dict]:
    """
    roda varios plugins ao mesmo tempo usando threads
    cada plugin vira uma thread, max_workers controla quantos rodam simultaneamente
    retorna lista de dicts com {name, output} na ordem que terminam
    """
    resultados = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {executor.submit(_executar_um, p, inputs): p for p in plugins}
        for futuro in as_completed(futuros):
            try:
                resultados.append(futuro.result())
            except Exception as e:
                plugin_nome = futuros[futuro].get("name", "?")
                resultados.append({"name": plugin_nome, "output": f"falha inesperada: {e}"})
    return resultados
