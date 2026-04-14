import glob
import re

files = glob.glob(r"d:\tesis\jhire\frontend\*.html")
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Matches <a ...> ... settings/Ajustes ... </a>
    content = re.sub(r'<a[^>]*>[\s\S]*?<span[^>]*>(?:settings|contact_support)</span>[\s\S]*?</a>\s*', '', content)
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print("Removed settings and support links.")
