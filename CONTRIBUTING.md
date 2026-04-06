# 🤝 Contributing to Colombo_SCAN

We welcome contributions! Whether it's adding a new OSINT plugin, fixing a bug, or improving documentation, here's how you can help.

## 🛠️ Adding New Plugins

Plugins are the heart of Colombo_SCAN. To add a new one:

1.  **Identify the tool:** Choose a reliable OSINT tool available as a Docker image (e.g., on Docker Hub).
2.  **Create a YAML file:** Place it in the appropriate `plugins/<category>/` directory.
3.  **Define the structure:**
    ```yaml
    name: "MyTool"
    category: "📧 Email Analysis"
    description: "Briefly explain what it does"
    image: "user/tool:tag"
    command: "tool-cli --target {alvo}" # Use {alvo} as the placeholder
    inputs:
      - id: alvo
        prompt: "Enter email:"
    timeout: 60
    safe: true
    ```
4.  **Test locally:** Run `./run_colombo.sh` and select your tool in **Manual Mode**.
5.  **Submit a Pull Request!**

## 🏗️ Core Contributions

-   **Code Quality:** We use standard Python logging (`core/logger.py`).
-   **Security:** Never commit API keys. Use the `.scan_auth.yaml` pattern.
-   **Testing:** Add unit tests to `tests/` for any new core logic.

## ⚖️ License
By contributing, you agree that your contributions will be licensed under the MIT License.
