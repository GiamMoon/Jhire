import glob
import os

files = glob.glob('d:/tesis/jhire/frontend/*.html')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Prevenir que el texto de los enlaces del sidebar haga wrap
    content = content.replace('transition-colors"><span', 'transition-colors whitespace-nowrap"><span')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print(f"Patched {len(files)} files.")
