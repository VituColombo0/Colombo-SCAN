import os
import yaml

PASTA = "plugins"

def load_plugins() -> list:
    if not os.path.exists(PASTA):
        os.makedirs(PASTA)
        
    plugins = []
    
    for root, _, arquivos in os.walk(PASTA):
        for arq in arquivos:
            if arq.endswith(".yaml") or arq.endswith(".yml"):
                caminho = os.path.join(root, arq)
                
                with open(caminho, 'r', encoding='utf-8') as f:
                    try:
                        cfg = yaml.safe_load(f)
                        if cfg and "name" in cfg:
                            plugins.append(cfg)
                    except Exception as e:
                        print(f"falha ao parsear o plugin {arq}: {e}")
    return sorted(plugins, key=lambda p: p.get("name", ""))
