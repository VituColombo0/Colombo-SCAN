#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Verifica se o ambiente virtual existe E se está saudável (consegue importar dependências)
if [ ! -d "$DIR/.venv" ] || ! "$DIR/.venv/bin/python3" -c "import questionary" &> /dev/null; then
    echo "[!] Ambiente virtual ausente ou quebrado (talvez a pasta mudou de nome?). Recriando..."
    rm -rf "$DIR/.venv" 2>/dev/null
    python3 -m venv "$DIR/.venv"
fi

source "$DIR/.venv/bin/activate"

# Instala dependências silenciosamente se o requirements existir
if [ -f "$DIR/requirements.txt" ]; then
    pip install -r "$DIR/requirements.txt" --quiet
fi

# Passa eventuais argumentos (como --alvo) para o main.py
python3 "$DIR/main.py" "$@"
