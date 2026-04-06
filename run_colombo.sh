#!/bin/bash
# Colombo_SCAN — Tactical Setup & Launcher
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "🕵️‍♂️  Iniciando Colombo_SCAN UI..."

# 1. Docker Check
if ! command -v docker &> /dev/null; then
    echo "❌ [ERRO] Docker não encontrado! Por favor, instale o Docker para rodar os plugins."
    exit 1
fi

# 2. Virtual Environment Setup
if [ ! -d "$DIR/.venv" ]; then
    echo "📦  Criando ambiente virtual Python..."
    python3 -m venv "$DIR/.venv"
fi

source "$DIR/.venv/bin/activate"

# 3. Dependencies Sync
if [ -f "$DIR/requirements.txt" ]; then
    echo "⚙️  Sincronizando dependências (Requirements)..."
    pip install -r "$DIR/requirements.txt" --quiet
fi

# 4. Auth Checker
if [ ! -f "$DIR/.scan_auth.yaml" ]; then
    echo "🔑  Criando template .scan_auth.yaml (lembre-se de preencher suas chaves)..."
    echo "# Configure suas API Keys aqui (este arquivo é ignorado pelo git)" > "$DIR/.scan_auth.yaml"
    echo "SHODAN_API_KEY: \"xxxxxx\"" >> "$DIR/.scan_auth.yaml"
fi

# 5. Launch
python3 "$DIR/main.py" "$@"
