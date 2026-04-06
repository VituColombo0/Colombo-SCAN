# 🕵️‍♂️ Colombo_SCAN v4.5 — Advanced OSINT Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker Support: Yes](https://img.shields.io/badge/Docker-Supported-cyan.svg)](https://www.docker.com/)

**Colombo_SCAN** is a modular, high-performance tactical reconnaissance and OSINT (Open Source Intelligence) framework. It automates information gathering by orchestrating specialized micro-tools within isolated Docker containers, allowing for a secure, scalable, and noise-resilient investigation process.

---

## ✨ Key Features

- **🚀 Concurrent Execution:** Processes multiple targets and plugins in parallel via `ThreadPoolExecutor`.
- **🛡️ Secure Sandboxing:** All investigative tools run in hardened Docker containers to prevent host contamination.
- **📁 Declarative Plugin System:** Add new tools by simply dropping a YAML configuration into the `plugins/` directory.
- **🧠 Smart Input Parser:** Automatically detects and normalizes inputs:
  - Emails, Phone Numbers, Domains/IPs, MAC Addresses.
  - Crypto Wallets (BTC, ETH, LTC), CPFs, CNPJs, Vehicle Plates (Mercosul/Classic).
- **🕸️ Recursive Analysis:** Automated "Deep Scans" that pivot through newly discovered entities (Emails ➡️ Usernames ➡️ Leaks).
- **📊 Professional Reporting:** Exports results into **Interactive HTML Graphs**, **PDF Dossiers**, and **JSON/CSV** formats.
- **🔌 API-First Architecture:** Integrated FastAPI server for remote Orchestration and integration with other SOC/NTI tools.

---

## 🏗️ Project Architecture

```text
Colombo_SCAN/
├── api/             # REST API for remote orchestration (FastAPI)
├── core/            # High-level engine, plugin runner, and data processing
├── scripts/         # Tactical utility scripts (expert mode, image checking)
├── plugins/         # Declarative YAML tool definitions (The brain of Colombo)
├── ui/              # Interactive CLI components powered by Rich & Questionary
├── data/            # Local SQLite storage for Case Management
├── logs/            # Centralized debug and execution logs
├── relatorios/      # Investigation artifacts (PDFs, Graphs, Raw data)
└── tests/           # Unit and integration test suites
```

---

## 🚀 Quick Start

### 1. Prerequisites
- [Docker Engine](https://docs.docker.com/get-docker/) (Ensure it's running)
- Python 3.10+

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/VituColombo0/Colombo-SCAN.git && cd Colombo-SCAN

# Run the automated setup and launch the CLI
./run_colombo.sh
```

### 3. Usage
- **Interactive Mode:** Simply run `./run_colombo.sh` and follow the menus.
- **Silent Scan:** `./run_colombo.sh --alvo 8.8.8.8`
- **API Mode:** `./run_colombo.sh --api` (Access docs at `http://localhost:8000/docs`)

---

## 🔐 Authentication
Sensitive API keys should be configured in `.scan_auth.yaml` (automatically ignored by git).
Example:
```yaml
SHODAN_API_KEY: "your_key_here"
VIRUSTOTAL_API_KEY: "your_key_here"
```

---

## 🤝 Contributing
Interested in adding a new tool? Check out [CONTRIBUTING.md](CONTRIBUTING.md).

## ⚖️ Disclaimer
*Colombo_SCAN is intended for legal investigations, bug bounty hunting, and ethical research. The authors are not responsible for misuse. Respect the TOS of all indexed services.*
