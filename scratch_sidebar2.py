import re

sidebar_template = """<!-- SIDEBAR -->
<aside class="fixed top-0 left-0 h-screen w-64 bg-surface border-r border-outline-variant/20 z-50 flex flex-col hidden md:flex shadow-xl">
    <div class="h-16 flex items-center px-6 border-b border-outline-variant/20 bg-surface-container-low">
        <span class="material-symbols-outlined text-primary text-3xl mr-2" style="font-variation-settings: 'FILL' 1;">precision_manufacturing</span>
        <span class="text-2xl font-black tracking-tighter text-primary bg-clip-text">JHIRE</span>
    </div>
    
    <nav class="flex-1 p-4 space-y-2 overflow-y-auto">
        <p class="text-[10px] uppercase font-bold text-outline tracking-widest pl-4 mb-2">Principal</p>
        <a href="dashboard.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">dashboard</span> Panel Central
        </a>
        <a href="inventario.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">inventory_2</span> Inventarios
        </a>
        <a href="admin_catalogo.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">category</span> Catálogo
        </a>
        
        <p class="text-[10px] uppercase font-bold text-outline tracking-widest pl-4 mb-2 mt-6">Comercial</p>
        <a href="ventas.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">point_of_sale</span> Ventas (POS)
        </a>
        <a href="crm.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">support_agent</span> CRM Clientes
        </a>
        <a href="facturacion.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">receipt_long</span> Facturación
        </a>

        <p class="text-[10px] uppercase font-bold text-outline tracking-widest pl-4 mb-2 mt-6">Administración</p>
        <a href="admin_usuarios.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">group</span> Gestor Usuarios
        </a>
        <a href="dashboard.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">analytics</span> Reportes y BI
        </a>
    </nav>
    
    <div class="p-4 border-t border-outline-variant/20">
        <a href="admin_perfil.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">settings</span> Mi Perfil
        </a>
        <button id="logoutBtn" class="w-full mt-2 flex items-center gap-3 px-4 py-3 text-error hover:bg-error/10 font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">logout</span> Salir
        </button>
    </div>
</aside>"""

for fn in ['crm.html', 'facturacion.html']:
    path = r'd:\tesis\jhire\frontend\\' + fn
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    # The broken block in crm.html and facturacion.html is:
    # <!-- SideNavBar -->
    # </div>
    # </aside>
    html = re.sub(r'<!-- SideNavBar -->\s*</div>\s*</aside>', sidebar_template, html)
    
    # Apply selection
    if fn == 'crm.html':
        html = html.replace('<a href="crm.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">\n            <span class="material-symbols-outlined">support_agent</span> CRM Clientes\n        </a>', '<a href="crm.html" class="flex items-center gap-3 px-4 py-3 bg-primary/10 text-primary font-bold rounded-xl shadow-sm transition-colors">\n            <span class="material-symbols-outlined">support_agent</span> CRM Clientes\n        </a>')
    elif fn == 'facturacion.html':
        html = html.replace('<a href="facturacion.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">\n            <span class="material-symbols-outlined">receipt_long</span> Facturación\n        </a>', '<a href="facturacion.html" class="flex items-center gap-3 px-4 py-3 bg-primary/10 text-primary font-bold rounded-xl shadow-sm transition-colors">\n            <span class="material-symbols-outlined">receipt_long</span> Facturación\n        </a>')

    # Quick check for <main class="flex-1 ml-64... vs <main class="ml-64 -> Should ensure padding is fine
    # They both have ml-64 already!
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
        print("Restored FULL sidebar on", fn)
