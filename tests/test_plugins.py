from core.plugin_manager import load_plugins
from core.runner import run_plugin
plugins = load_plugins()
test_plugin = plugins[0]
print(f"Testando: {test_plugin['name']}")
res = run_plugin(test_plugin, {'alvo': 'google.com'})
print(res)
