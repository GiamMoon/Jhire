import re

# 1. Full sidebar injection
new_sidebar = """<!-- SIDEBAR -->
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
        <a href="ventas.html" class="flex items-center gap-3 px-4 py-3 bg-primary/10 text-primary font-bold rounded-xl shadow-sm transition-colors">
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

path = r"d:\tesis\jhire\frontend\ventas.html"
html = open(path, "r", encoding="utf-8").read()

# Replace the broken sidebar first
html = re.sub(r'<!-- SideNavBar -->\s*</div>\s*</aside>', new_sidebar, html)

# 2. Translations
html = html.replace("Search sales, clients or products...", "Buscar ventas, clientes o productos...")
html = html.replace("Filters", "Filtros")
html = html.replace("New Quotation", "Nueva Venta Rápida")
html = html.replace("Last 30 Días", "Últimos 30 Días")
html = html.replace("Leads", "Ventas Diarias")
html = html.replace("Opportunities", "Ventas Semanales")
html = html.replace("Quotations", "Ventas Mensuales")
html = html.replace("Closed", "Ticket Promedio")
html = html.replace("Restante: $240k", "Restante: S/ 50k")
html = html.replace("View All", "Ver Todo")
html = html.replace("Recent Ventas Activity", "Últimas Transacciones (POS)")
html = html.replace("Amount", "Monto")
html = html.replace("Client", "Cajero/Cliente")
html = html.replace("Status", "Estado")
html = html.replace("Ventas & Prospecting", "Ventas (Punto de Venta POS)")

# 3. Inject IDs so app.js loadDynamicCRM populates it
# Wait, actually loadDynamicCRM uses 'crmRecentSalesBody' etc. 
# They share the structure so we can use the exact same IDs to populate DB data easily.
html = html.replace('<tbody class="divide-y divide-slate-50">', '<tbody class="divide-y divide-slate-50" id="crmRecentSalesBody">')
html = html.replace('<div class="space-y-3">', '<div class="space-y-3" id="crmProductList">', 1)
html = html.replace('<div class="flex items-stretch h-32 w-full gap-1">', '<div class="flex items-stretch h-32 w-full gap-1" id="crmFunnelContainer">')

open(path, "w", encoding="utf-8").write(html)
print("Ventas fixed.")
