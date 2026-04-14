import os
import glob
import re

files_to_patch = [
    r'd:\tesis\jhire\frontend\sobre_nosotros.html',
    r'd:\tesis\jhire\frontend\politica_privacidad.html',
    r'd:\tesis\jhire\frontend\terminos_condiciones.html',
    r'd:\tesis\jhire\frontend\contacto_comercial.html'
]

link_mis_pedidos = '<a class="relative text-on-surface hover:text-primary font-bold text-[13px] tracking-wider uppercase transition-all duration-300" href="mis_pedidos.html">Mis Pedidos</a>'

for filepath in files_to_patch:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Target:
        # <a class="relative text-on-surface hover:text-primary font-bold text-[13px] tracking-wider uppercase transition-all duration-300" href="catalogo_usuario.html">Catálogo</a>
        # We need to append the Mis Pedidos link right after if it is missing
        
        # Or look for exact block
        if "href=\"mis_pedidos.html\"" not in content:
            # Let's target the exact link for Catalogo
            pattern1 = r'(<a[^>]*href="catalogo_usuario.html"[^>]*>Catálogo</a>)'
            pattern2 = r'(<a[^>]*href="catalogo_usuario.html"[^>]*>Catálogo</a>)'
            
            # Since my previous templates were identical
            if re.search(pattern1, content):
                content = re.sub(pattern1, r'\1\n            ' + link_mis_pedidos, content)
                
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
print("Navbar patched.")
