import os
import re

files_older = ['crm.html', 'ventas.html', 'facturacion.html']
files_newer = ['inventario.html', 'admin_catalogo.html', 'admin_usuarios.html', 'admin_perfil.html', 'dashboard.html']

for filename in files_older:
    path = os.path.join('d:/tesis/jhire/frontend', filename)
    if not os.path.exists(path): continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find: Eduardo Méndez + image tag
    pattern = r'<div class="text-right">\s*<p class=".*?text-blue-900">Eduardo Méndez</p>\s*<p class=".*?text-slate-500">Ventas Manager</p>\s*</div>\s*<img.*?>'
    
    replacement = """<div class="text-right">
<p id="headerUserName" class="text-xs font-bold text-blue-900">Cargando...</p>
<p id="headerUserRole" class="text-[10px] text-slate-500">...</p>
</div>
<img id="userAvatar" src="https://ui-avatars.com/api/?name=User&background=003461&color=fff" class="w-9 h-9 rounded-full object-cover ring-2 ring-primary/10" />"""

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Another variant just in case. In facturacion.html it might be inside <div class="flex items-center gap-3">
    # Wait, facturacion.html does not have Eduardo Mendez.
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated Older Profile in {filename}")

for filename in files_newer:
    path = os.path.join('d:/tesis/jhire/frontend', filename)
    if not os.path.exists(path): continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern for newer UI where Admin Root is inside
    pattern2 = r'<img(?:(?!<img).)*?src="https://ui-avatars.com(?:(?!<img).)*?Admin\+Root.*?"(?:(?!<img).)*?>\s*<div class="hidden md:block text-left relative top-\[1px\]">\s*<p .*?>Admin Root</p>\s*<p .*?>Operaciones</p>\s*</div>'
    
    replacement2 = """<img id="userAvatar" src="https://ui-avatars.com/api/?name=User&background=003461&color=fff" class="w-8 h-8 rounded-full border-2 border-primary/20 object-cover">
                <div class="hidden md:block text-left relative top-[1px]">
                    <p id="headerUserName" class="text-[11px] font-black text-on-surface uppercase tracking-wide leading-none">Cargando...</p>
                    <p id="headerUserRole" class="text-[9px] text-primary font-bold uppercase tracking-widest leading-none mt-[2px]">...</p>
                </div>"""
                
    new_content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated Newer Profile in {filename}")
