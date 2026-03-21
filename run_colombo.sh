#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$DIR/.venv/bin/activate"
pip install fpdf2 --quiet 2>/dev/null
python3 "$DIR/main.py"
