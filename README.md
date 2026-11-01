# Colombo_SCAN: Framework Tático de Inteligência e OSINT

Framework modular de alta performance para reconhecimento tático, coleta de fontes abertas (OSINT) e análise forense digital, orquestrando ferramentas especializadas em contêineres Docker isolados com execução concorrente e geração de dossiês.

[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Containers: Docker](https://img.shields.io/badge/Sandboxing-Docker%20Hardened-2496ED.svg)](https://www.docker.com/)
[![API: FastAPI](https://img.shields.io/badge/API-FastAPI%20Swagger-009688.svg)](https://fastapi.tiangolo.com/)
[![Interface: Rich & Questionary](https://img.shields.io/badge/CLI-Rich%20%26%20Questionary-darkgreen.svg)](https://github.com/Textualize/rich)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Visão Geral

O **Colombo_SCAN** automatiza o ciclo completo de inteligência investigativa em fontes abertas. Ele elimina a contaminação do ambiente host executando ferramentas de terceiros em contêineres Docker efêmeros, normaliza entidades de alvos heterogêneos e consolida os achados em relatórios visuais com grafos de relacionamentos e sumários executivos.

```
                     Entrada Bruta do Investigador
     (Email, Domínio, IP, CPF, CNPJ, Placa de Veículo, Crypto Wallet)
                                   │
                                   ▼
                   [ Smart Entity Parser & Normalizer ]
                       Identificação e validação
                                   │
                                   ▼
                   [ Motor Central (Core Engine) ]
              Orquestração paralela via ThreadPoolExecutor
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
   [ Plugin YAML 1 ]         [ Plugin YAML 2 ]         [ Plugin YAML N ]
   Docker Sandbox A          Docker Sandbox B          Docker Sandbox N
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                                   ▼
                   [ Gestão de Casos (SQLite) ]
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
[ Dossiês & Grafos ]                               [ API REST Integrada ]
PDFs, HTML Graphs e JSON                           FastAPI (:8000/docs)
```

---

## Capacidades e Recursos Centrais

### 1. Parser Inteligente de Alvos
Reconhece e valida dinamicamente diferentes tipos de alvos no momento da entrada:
- **Identificadores Digitais:** Endereços de e-mail, nomes de usuário (handles), números de telefone internacionais (E.164), domínios, subdomínios, endereços IPv4/IPv6 e blocos CIDR.
- **Identificadores Nacionais:** Validação de formato e dígitos verificadores de CPF e CNPJ.
- **Placas de Veículos:** Padrão Mercosul e formato clássico brasileiro de três letras.
- **Criptoativos:** Endereços de carteiras Bitcoin (Legacy, SegWit e Bech32), Ethereum e Litecoin.

### 2. Sandboxing Estrito via Docker
Todas as ferramentas investigativas externas (scrapers, scanners de portas, analisadores de metadados de arquivos e verificadores de vazamentos) executam em contêineres isolados com permissões restritas e descarte automático após a conclusão da tarefa.

### 3. Arquitetura Declarativa de Plugins
Novas ferramentas podem ser adicionadas sem alterar o código principal da aplicação, criando um manifesto YAML no diretório `plugins/`:

```yaml
name: "shodan_lookup"
category: "network"
target_types: ["ip", "domain"]
docker_image: "colombo/shodan-probe:latest"
command: "python run.py --target {target}"
requires_auth: true
auth_key: "SHODAN_API_KEY"
```

### 4. Varredura Recursiva (Deep Scan Pivot)
Permite ao investigador autorizar desdobramentos automáticos: ao identificar um novo e-mail ou username em um vazamento de banco de dados, o motor adiciona o novo nó à fila de investigação com rastreamento de linhagem.

### 5. Geração de Relatórios e Evidências
- **Grafos Interativos em HTML:** Visualização de nós e arestas conectando alvos, infraestruturas compartilhadas e entidades relacionadas.
- **Dossiês Formatais em PDF:** Relatórios consolidados com hash de integridade, carimbos de data/hora (*timestamps*) e classificação de criticidade.
- **Exportação Estruturada:** Dados tabulares em formato CSV e JSON para ingestão em plataformas SIEM/SOC.

---

## Modos de Operação

### Modo Interativo CLI
Interface interativa em terminal com menus navegáveis:
```bash
./run_colombo.sh
```

### Modo Silencioso / Linha de Comando (Scripted)
Execução direta para scripts e rotinas de triagem:
```bash
# Investigação de endereço IP
./run_colombo.sh --alvo 198.51.100.24

# Varredura recursiva de domínio com saída em PDF
./run_colombo.sh --alvo example.com --deep --pdf
```

### Modo Servidor / API REST
Inicia o backend em **FastAPI** para integração com outras ferramentas:
```bash
./run_colombo.sh --api
```
A documentação interativa OpenAPI/Swagger estará disponível em `http://localhost:8000/docs`.

---

## Pré-requisitos de Instalação

- **Linux** (testado em Ubuntu 22.04+, Debian 12 e Kali Linux) ou **WSL2** no Windows
- **Docker Engine** e Docker Compose instalados e com daemon ativo
- **Python 3.10** ou superior

---

## Instalação e Inicialização

```bash
# Clone o repositório
git clone https://github.com/VituColombo0/Colombo-SCAN.git
cd Colombo-SCAN

# Permissão de execução no script utilitário
chmod +x run_colombo.sh

# Inicialize o ambiente (instala venv, dependências e compila contêineres base)
./run_colombo.sh
```

---

## Gerenciamento de Chaves de API

Chaves de serviços de inteligência externos são gerenciadas no arquivo `.scan_auth.yaml` (ignorado automaticamente pelo git):

```yaml
# .scan_auth.yaml
SHODAN_API_KEY: "SUA_CHAVE_AQUI"
VIRUSTOTAL_API_KEY: "SUA_CHAVE_AQUI"
SECURITYTRAILS_API_KEY: "SUA_CHAVE_AQUI"
HIBP_API_KEY: "SUA_CHAVE_AQUI"
```

Variáveis de ambiente gerais podem ser definidas em `.env` a partir do template `.env.example`:
```bash
cp .env.example .env
```

---

## Estrutura do Repositório

```text
Colombo-SCAN/
├── api/              # Endpoints da API REST em FastAPI
├── core/             # Engine central, normalizadores e executores concorrentes
├── plugins/          # Definições declarativas de plugins em formato YAML
├── ui/               # Componentes de interface de linha de comando (Rich/Questionary)
├── scripts/          # Utilitários de verificação e rotinas de manutenção
├── data/             # Armazenamento SQLite local de casos e sessões
├── logs/             # Logs de auditoria e depuração técnica
├── relatorios/       # Dossiês gerados, grafos HTML e exportações JSON/CSV
├── tests/            # Testes unitários e de integração
├── run_colombo.sh    # Script central de inicialização e deploy
├── main.py           # Entrypoint do interpretador CLI
└── README.md         # Documentação técnica do framework
```

---

## Termo de Uso e Responsabilidade Legal

O **Colombo_SCAN** foi desenvolvido exclusivamente para finalidades defensivas, perícia computacional legalmente autorizada, treinamentos acadêmicos e auditorias autorizadas de segurança (Bug Bounty com autorização expressa). Os autores não se responsabilizam pelo uso inadequado ou ilícito das ferramentas integradas. Certifique-se de cumprir os termos de serviço (ToS) de todas as APIs consultadas.
