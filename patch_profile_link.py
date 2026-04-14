import os
import glob

link_html = """                <a href="perfil_usuario.html" class="w-full text-left px-5 py-3 text-sm text-on-surface hover:bg-surface-container-high font-bold flex items-center gap-3 transition-colors">
                    <span class="material-symbols-outlined text-[18px]">person</span> Mi Perfil
                </a>
                <hr class="border-outline/10 mx-2">
                <button id="logoutBtn\""""

for filepath in glob.glob(r'd:\tesis\jhire\frontend\*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'id="logoutBtn"' in content and "perfil_usuario.html" not in content:
        content = content.replace('<button id="logoutBtn"', link_html)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {filepath}")
