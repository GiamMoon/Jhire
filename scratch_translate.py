import re

html = open(r"d:\tesis\jhire\frontend\crm.html", "r", encoding="utf-8").read()

html = html.replace("Search sales, clients or products...", "Buscar ventas, clientes o productos...")
html = html.replace("Filters", "Filtros")
html = html.replace("New Quotation", "Nueva Cotización")
html = html.replace("Last 30 Días", "Últimos 30 Días")
html = html.replace("Leads", "Prospectos")
html = html.replace("Opportunities", "Oportunidades")
html = html.replace("Quotations", "Cotizaciones")
html = html.replace("Closed", "Cerradas")
html = html.replace("Restante: $240k", "Restante: S/ 50k")
html = html.replace("View All", "Ver Todo")
html = html.replace("Recent Ventas Activity", "Ventas Recientes")
html = html.replace("Amount", "Monto")
html = html.replace("Client", "Cliente")
html = html.replace("Status", "Estado")
html = html.replace('<tbody class="divide-y divide-slate-50">', '<tbody class="divide-y divide-slate-50" id="crmRecentSalesBody">')
html = html.replace('<div class="space-y-3">', '<div class="space-y-3" id="crmProductList">', 1)
html = html.replace('<div class="flex items-stretch h-32 w-full gap-1">', '<div class="flex items-stretch h-32 w-full gap-1" id="crmFunnelContainer">')

open(r"d:\tesis\jhire\frontend\crm.html", "w", encoding="utf-8").write(html)
print("CRM translation done.")
