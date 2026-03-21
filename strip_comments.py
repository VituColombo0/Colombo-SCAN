import os
import re

def strip_comments(directory):
    for root, _, files in os.walk(directory):
        if '.venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = re.sub(r'(?m)^\s*#.*?\n', '', content)
                content = re.sub(r'(?m)[ \t]+#.*$', '', content)
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)

if __name__ == '__main__':
    strip_comments('.')
