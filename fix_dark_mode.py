import os
import glob
import re

frontend_path = r"d:\tesis\jhire\frontend\*.html"
filepaths = glob.glob(frontend_path)

for filepath in filepaths:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replacements to support dynamic dark mode gracefully
    # Replace bg-white with bg-surface
    content = re.sub(r'\bbg-white\b', 'bg-surface', content)
    
    # Replace borders that might be white/black
    content = content.replace('border-white/10', 'border-outline/10')

    # Re-write the buttons in perfil_usuario.html to have IDs so app.js can highlight them
    if 'perfil_usuario.html' in filepath:
        # Give them IDs to toggle active state
        content = content.replace('onclick="window.changeTheme(\'light\')"', 'id="themeBtn-light" onclick="window.changeTheme(\'light\')"')
        content = content.replace('onclick="window.changeTheme(\'dark\')"', 'id="themeBtn-dark" onclick="window.changeTheme(\'dark\')"')
        content = content.replace('onclick="window.changeTheme(\'auto\')"', 'id="themeBtn-auto" onclick="window.changeTheme(\'auto\')"')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Dark mode hardcoded classes fixed.")
