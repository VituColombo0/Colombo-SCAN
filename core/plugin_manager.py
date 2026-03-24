"""
Colombo Scanner — Plugin Manager with Schema Validation
Loads YAML plugin definitions with validation, normalization, and error reporting.
"""
import os
import re
import yaml
from core.logger import get_logger

log = get_logger("plugin_manager")

PASTA = "plugins"

# Required fields for a valid plugin
REQUIRED_FIELDS = ["name", "category", "command"]

# Known variable patterns that should be normalized
VARIABLE_ALIASES = {
    "target": "alvo",
    "domain": "alvo",
    "host": "alvo",
    "query": "alvo",
    "url": "alvo",
}


def _validate_plugin(cfg: dict, filename: str) -> list[str]:
    """
    Validates a plugin config dict against the schema.
    Returns a list of warnings (empty = valid).
    """
    warnings = []

    for field in REQUIRED_FIELDS:
        if field not in cfg:
            warnings.append(f"Campo obrigatório '{field}' ausente")

    # Check for docker run duplication in command
    command = cfg.get("command", "")
    if cfg.get("image") and "docker run" in command:
        warnings.append(
            f"Plugin tem 'image' definido E 'docker run' no command — "
            "o runner já faz docker run. Removendo duplicação automaticamente."
        )

    # Check for -it flag (breaks non-interactive execution)
    if "-it " in command or " -it" in command:
        warnings.append("Flag '-it' detectada no command — removida (não funciona em execução não-interativa)")

    return warnings


def _normalize_plugin(cfg: dict, filename: str) -> dict:
    """
    Normalizes plugin configuration:
    - Fixes variable names ({target} → {alvo})
    - Removes docker run from command if 'image' is set  
    - Strips -it flags
    - Adds default fields
    """
    command = cfg.get("command", "")
    image = cfg.get("image", "")

    # 1. Extract image from docker run if embedded and no 'image' field
    if not image and "docker run" in command:
        # Pattern: docker run --rm [flags] IMAGE ARGS
        match = re.match(
            r'docker\s+run\s+(?:--rm\s+)?(?:-[a-z]+\s+)*([a-zA-Z0-9_./-]+(?::[a-zA-Z0-9._-]+)?)\s*(.*)',
            command
        )
        if match:
            cfg["image"] = match.group(1)
            cfg["command"] = match.group(2).strip()
            log.info(f"[{filename}] Extraída image '{cfg['image']}' do command")

    # 2. Remove docker run from command if image is already set
    elif image and "docker run" in command:
        # Remove the docker run prefix, keep just the args
        cleaned = re.sub(
            r'docker\s+run\s+(?:--rm\s+)?(?:-[a-z]+\s+)*[a-zA-Z0-9_./-]+(?::[a-zA-Z0-9._-]+)?\s*',
            '',
            command
        ).strip()
        if cleaned:
            cfg["command"] = cleaned
        log.info(f"[{filename}] Removido 'docker run' duplicado do command")

    # 3. Remove -it flag
    cfg["command"] = re.sub(r'\s*-it\s+', ' ', cfg.get("command", "")).strip()

    # 4. Normalize variable names
    for old_var, new_var in VARIABLE_ALIASES.items():
        pattern = "{" + old_var + "}"
        if pattern in cfg["command"]:
            cfg["command"] = cfg["command"].replace(pattern, "{" + new_var + "}")
            log.debug(f"[{filename}] Normalizado {{{old_var}}} → {{{new_var}}}")

    # 5. Add default fields
    cfg.setdefault("description", f"{cfg.get('name', filename)} plugin")
    cfg.setdefault("timeout", 300)
    cfg.setdefault("version", "latest")

    # 6. Ensure inputs field exists with at least 'alvo'
    if "inputs" not in cfg:
        cfg["inputs"] = [{"id": "alvo", "prompt": f"Alvo para {cfg.get('name', 'ferramenta')}:"}]

    return cfg


def load_plugins() -> list:
    """
    Loads all YAML plugins from the plugins directory.
    Validates and normalizes each plugin, logging warnings for issues.
    """
    if not os.path.exists(PASTA):
        os.makedirs(PASTA)
        log.warning(f"Diretório '{PASTA}' criado (estava vazio)")

    plugins = []
    total_files = 0
    invalid_count = 0

    for root, _, arquivos in os.walk(PASTA):
        for arq in arquivos:
            if not (arq.endswith(".yaml") or arq.endswith(".yml")):
                continue

            total_files += 1
            caminho = os.path.join(root, arq)

            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)
            except Exception as e:
                log.error(f"Falha ao parsear {arq}: {e}")
                invalid_count += 1
                continue

            if not cfg or not isinstance(cfg, dict):
                log.warning(f"Plugin vazio ou inválido: {arq}")
                invalid_count += 1
                continue

            # Validate
            warnings = _validate_plugin(cfg, arq)
            
            # Check for critical missing fields
            has_critical_error = False
            for w in warnings:
                if "obrigatório" in w:
                    log.error(f"[{arq}] {w}")
                    has_critical_error = True
                else:
                    log.warning(f"[{arq}] {w}")

            if has_critical_error:
                invalid_count += 1
                continue

            # Normalize
            cfg = _normalize_plugin(cfg, arq)
            cfg["_source_file"] = caminho
            plugins.append(cfg)

    log.info(f"Plugins carregados: {len(plugins)}/{total_files} válidos ({invalid_count} com erros)")

    return sorted(plugins, key=lambda p: p.get("name", ""))
