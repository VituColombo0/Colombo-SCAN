import yaml
import os
import urllib.request
import json
from concurrent.futures import ThreadPoolExecutor

PASTA = 'plugins'
images_to_check = set()

for root, _, files in os.walk(PASTA):
    for f in files:
        if f.endswith('.yaml'):
            path = os.path.join(root, f)
            with open(path, 'r') as file:
                try:
                    cfg = yaml.safe_load(file)
                    img = cfg.get('image')
                    if img:
                        images_to_check.add((path, img.split(':')[0]))
                except Exception:
                    pass

def check_image(item):
    path, img = item
    if '/' not in img:
        img = 'library/' + img
    url = f"https://hub.docker.com/v2/repositories/{img}/"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            if resp.status == 200:
                return True, path
    except Exception:
        pass
    return False, path

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(check_image, images_to_check))

valid = [p for s, p in results if s]
invalid = [p for s, p in results if not s]

print(f"Valid: {len(valid)}, Invalid: {len(invalid)}")
for path in invalid:
    os.remove(path)
print("Removed invalid plugins.")
