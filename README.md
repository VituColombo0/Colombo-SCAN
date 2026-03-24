# OSINT Scanner

Extensible and parallelized OSINT toolkit built with Python and Docker.

## Dependencies

- Python 3.10+
- Docker
- PyYAML, questionary, rich, fpdf2, python-dotenv
- fastapi, uvicorn (necessários para o modo --api)

## Initialization

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install PyYAML questionary rich fpdf2
./run_colombo.sh
```

## Architecture Overview

- `main.py`: CLI entrypoint.
- `core/`: Execution engine, concurrency management, and PDF/Graph report generation.
- `plugins/`: Declarative YAML configurations representing individual OSINT tools.

## Supported Inputs

- Email Addresses
- Phone Numbers
- URLs / Domains
- IPv4 / IPv6 Addresses
- Crypto Wallets (BTC, ETH, LTC)
- Social Usernames
- Files (Hashes, Documents, Images)
- Corporate Entities (CNPJ)
- Flight Identifiers
- Vehicle Plates / Chassis (VIN)

## Plugin Configuration (YAML)

Plugins define Docker execution contexts. New tools are integrated by adding definitions to the `plugins/` directory.

```yaml
name: GenericTool
category: Networking
type: docker
image: namespace/tool:latest
command: "-u {alvo}"
inputs:
  - id: alvo
    prompt: "Target:"
```
