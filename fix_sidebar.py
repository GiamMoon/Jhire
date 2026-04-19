import os
import re

files_to_fix = [
    'dashboard.html',
    'inventario.html',
    'admin_catalogo.html',
    'ventas.html',
    'crm.html',
    'facturacion.html',
    'admin_usuarios.html',
    'admin_perfil.html'
]

nav_template = """<nav class="flex-1 p-4 space-y-2 overflow-y-auto">
        <p class="text-[10px] uppercase font-bold text-outline tracking-widest pl-4 mb-2">Principal</p>
        <a href="dashboard.html" class="flex items-center gap-3 px-4 py-3 {dashboard} rounded-xl">
            <span class="material-symbols-outlined">dashboard</span> Panel Central
        </a>
        <a href="inventario.html" class="flex items-center gap-3 px-4 py-3 {inventario} rounded-xl">
            <span class="material-symbols-outlined">inventory_2</span> Inventarios
        </a>
        <a href="admin_catalogo.html" class="flex items-center gap-3 px-4 py-3 {catalogo} rounded-xl">
            <span class="material-symbols-outlined">category</span> Catálogo
        </a>
        
        <p class="text-[10px] uppercase font-bold text-outline tracking-widest pl-4 mb-2 mt-6">Comercial</p>
        <a href="ventas.html" class="flex items-center gap-3 px-4 py-3 {ventas} rounded-xl">
            <span class="material-symbols-outlined">point_of_sale</span> Ventas (POS)
        </a>
        <a href="crm.html" class="flex items-center gap-3 px-4 py-3 {crm} rounded-xl">
            <span class="material-symbols-outlined">support_agent</span> CRM Clientes
        </a>
        <a href="facturacion.html" class="flex items-center gap-3 px-4 py-3 {facturacion} rounded-xl">
            <span class="material-symbols-outlined">receipt_long</span> Facturación
        </a>

        <p class="text-[10px] uppercase font-bold text-outline tracking-widest pl-4 mb-2 mt-6">Administración</p>
        <a href="admin_usuarios.html" class="flex items-center gap-3 px-4 py-3 {usuarios} rounded-xl">
            <span class="material-symbols-outlined">group</span> Gestor Usuarios
        </a>
        <a href="dashboard.html" class="flex items-center gap-3 px-4 py-3 {reportes} rounded-xl">
            <span class="material-symbols-outlined">analytics</span> Reportes y BI
        </a>
    </nav>"""

active_class = "bg-primary/10 text-primary font-bold shadow-sm"
inactive_class = "text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold transition-colors"

mapping = {
    'dashboard.html': 'dashboard',
    'inventario.html': 'inventario',
    'admin_catalogo.html': 'catalogo',
    'ventas.html': 'ventas',
    'crm.html': 'crm',
    'facturacion.html': 'facturacion',
    'admin_usuarios.html': 'usuarios'
}

for filename in files_to_fix:
    path = os.path.join('d:/tesis/jhire/frontend', filename)
    if not os.path.exists(path):
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '<nav class="flex-1 p-4 space-y-2 overflow-y-auto">' not in content:
        continue
    
    fmt_dict = {k: inactive_class for k in mapping.values()}
    fmt_dict['reportes'] = inactive_class
    
    if filename in mapping:
        fmt_dict[mapping[filename]] = active_class
        
    custom_nav = nav_template.format(**fmt_dict)
    
    new_content = re.sub(r'<nav class="flex-1 p-4 space-y-2 overflow-y-auto">.*?</nav>', custom_nav, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filename}")
