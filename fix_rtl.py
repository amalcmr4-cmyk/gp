import os
import re

css_files = [f for f in os.listdir('.') if f.endswith('.css')]
for f in css_files:
    with open(f, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    new_lines = []
    changed = False
    for line in lines:
        if '[dir="rtl"]' in line and 'row-reverse' in line:
            new_line = re.sub(r'flex-direction:\s*row-reverse;?', '', line)
            new_lines.append(new_line)
            changed = True
        else:
            new_lines.append(line)
            
    if changed:
        with open(f, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)
        print(f'Fixed {f}')
