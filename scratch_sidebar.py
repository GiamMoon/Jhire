import re

new_nav = """    <nav class="flex-1 p-4 space-y-2 overflow-y-auto">
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
    </nav>"""

files = ['dashboard.html', 'inventario.html', 'admin_catalogo.html', 'admin_usuarios.html', 'admin_perfil.html', 'ventas.html', 'crm.html', 'facturacion.html']
for fn in files:
    try:
        path = 'd:\\tesis\\jhire\\frontend\\' + fn
        html = open(path, 'r', encoding='utf-8').read()
        html = re.sub(r'<nav class="flex-1 p-4 space-y-2 overflow-y-auto">.*?</nav>', new_nav, html, flags=re.DOTALL)
        
        # Also fix any "bg-primary/10" selected states that we just wiped, based on the filename!
        if fn == 'dashboard.html':
            html = html.replace('<a href="dashboard.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">\n            <span class="material-symbols-outlined">dashboard</span> Panel Central\n        </a>', '<a href="dashboard.html" class="flex items-center gap-3 px-4 py-3 bg-primary/10 text-primary font-bold rounded-xl shadow-sm transition-colors">\n            <span class="material-symbols-outlined">dashboard</span> Panel Central\n        </a>')
        elif fn == 'crm.html':
            html = html.replace('<a href="crm.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">\n            <span class="material-symbols-outlined">support_agent</span> CRM Clientes\n        </a>', '<a href="crm.html" class="flex items-center gap-3 px-4 py-3 bg-primary/10 text-primary font-bold rounded-xl shadow-sm transition-colors">\n            <span class="material-symbols-outlined">support_agent</span> CRM Clientes\n        </a>')
        elif fn == 'facturacion.html':
             html = html.replace('<a href="facturacion.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">\n            <span class="material-symbols-outlined">receipt_long</span> Facturación\n        </a>', '<a href="facturacion.html" class="flex items-center gap-3 px-4 py-3 bg-primary/10 text-primary font-bold rounded-xl shadow-sm transition-colors">\n            <span class="material-symbols-outlined">receipt_long</span> Facturación\n        </a>')
        
        open(path, 'w', encoding='utf-8').write(html)
        print('Updated', fn)
    except Exception as e:
        print('Error', fn, e)
