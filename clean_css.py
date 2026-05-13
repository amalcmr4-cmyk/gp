import os
import re

css_files = [f for f in os.listdir('.') if f.endswith('.css')]
for f in css_files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remove empty rulesets like [dir="rtl"] .class { } or [dir="rtl"] .class {\n}
    new_content = re.sub(r'\[dir="rtl"\][^{]+\{\s*\}', '', content)
    
    # Remove duplicate newlines
    new_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_content)
    
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Cleaned {f}')
