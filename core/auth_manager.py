import yaml
import os

AUTH_FILE = ".scan_auth.yaml"

def get_auth_env() -> dict:
    """Carrega as variaveis de autenticacao do arquivo YAML principal"""
    if not os.path.exists(AUTH_FILE):
        return {}
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def create_auth_template():
    """Gera um template de Shadow Auth se ele nao existir"""
    if not os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            f.write("# COLOMBO SCANNER - Gerenciador Universal de Sessoes (Shadow Auth)\n"
                    "# Insira seus cookies e tokens aqui. \n"
                    "# Eles serao injetados ENVIROMENT VARIABLES diretamente no shell/docker dos plugins.\n\n"
                    "github_token: 'ghp_xxxxxx'\n"
                    "instagram_sessionid: 'xxxxxx'\n"
                    "twitter_auth_token: 'xxxxxx'\n"
                    "shodan_api_key: 'xxxxxx'\n")

# Gerar template logo no load do modulo
create_auth_template()
