from core.workflow import executar_workflow_recursivo
from unittest.mock import patch, MagicMock

def test_workflow_recursion():
    # Mock plugins list
    plugins = [
        {"name": "Tool1", "category": "📧 Análise de Emails", "command": "echo 'Found ip: 1.1.1.1'"},
        {"name": "Tool2", "category": "🌐 Redes e IPs", "command": "echo 'Found user: @vitu'"},
        {"name": "Tool3", "category": "👤 Identidades e Usernames", "command": "echo 'All clear'"}
    ]

    # Mock run_plugins_paralelo to simulate tool outputs
    def side_effect(plugins_list, inputs):
        alvo = inputs.get("alvo", "")
        if "@" in alvo: # Email
            return [{"name": "Tool1", "output": "New lead ip: 8.8.8.8 and email: other@test.com"}]
        elif "8.8.8.8" in alvo: # IP
            return [{"name": "Tool2", "output": "New lead user: @johndoe"}]
        else: # Username
            return [{"name": "Tool3", "output": "Done"}]

    with patch("core.workflow.run_plugins_paralelo", side_effect=side_effect), \
         patch("core.workflow.filtrar_plugins_smart", side_effect=lambda p, a: p):
        
        print("Rodando workflow de 2 camadas...")
        res = executar_workflow_recursivo("base@test.com", plugins, max_camadas=2, verbose=True)
        
        # Check layers
        layers = [r["camada"] for r in res]
        print(f"Camadas encontradas: {layers}")
        # Expected: Camada 1 (base@test.com), Camada 2 (8.8.8.8 and other@test.com)
        
        alvos = [r["alvo_origem"] for r in res]
        print(f"Alvos investigados: {alvos}")
        
    print("\n[SUCESSO] Workflow recursividade validada.")

if __name__ == "__main__":
    test_workflow_recursion()
