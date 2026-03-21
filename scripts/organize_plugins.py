import os
import yaml
import shutil

PASTA = "plugins"

def organize_plugins():
    for f in os.listdir(PASTA):
        path = os.path.join(PASTA, f)
        if os.path.isfile(path) and (f.endswith(".yaml") or f.endswith(".yml")):
            with open(path, 'r', encoding='utf-8') as file:
                try:
                    cfg = yaml.safe_load(file)
                    cat = cfg.get("category", "Outros")
                    
                    # Limpa emojis e caracteres problemáticos da categoria para criar folder
                    clean_cat = "".join([c if c.isalnum() or c in " &_-/" else "" for c in cat]).strip()
                    clean_cat = clean_cat.replace(" ", "_").replace("/", "-").lower()

                    target_dir = os.path.join(PASTA, clean_cat)
                    os.makedirs(target_dir, exist_ok=True)
                    
                    shutil.move(path, os.path.join(target_dir, f))
                except Exception as e:
                    print(f"Erro no {f}: {e}")

if __name__ == '__main__':
    organize_plugins()
