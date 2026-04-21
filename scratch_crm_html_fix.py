import re

path = r'd:\tesis\jhire\frontend\crm.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# Fix the Top Buttons
html = html.replace(
    '<button class="flex items-center gap-2 px-4 py-2.5 bg-surface-container-low text-primary font-semibold rounded-md hover:bg-surface-container-high transition-colors">\n<span class="material-symbols-outlined text-lg">filter_list</span>\n<span>Filtros</span>\n</button>',
    '<button onclick="Swal.fire(\'Filtros de Perfil\', \'Módulo de filtrado avanzado de clientes en desarrollo.\', \'info\')" class="flex items-center gap-2 px-4 py-2.5 bg-surface-container-low text-primary font-semibold rounded-md hover:bg-surface-container-high transition-colors">\n<span class="material-symbols-outlined text-lg">filter_alt</span>\n<span>Filtrar</span>\n</button>'
)

html = html.replace(
    '<button class="flex items-center gap-2 px-6 py-2.5 bg-primary text-white font-bold rounded-md shadow-lg shadow-primary/20 active:scale-95 transition-all">\n<span class="material-symbols-outlined text-lg">add_shopping_cart</span>\n<span>Nueva Cotización</span>\n</button>',
    '<button onclick="Swal.fire(\'Nuevo Registro\', \'Apertura rápida de cuentas comerciales.\', \'success\')" class="flex items-center gap-2 px-6 py-2.5 bg-primary text-white font-bold rounded-md shadow-lg shadow-primary/20 active:scale-95 transition-all">\n<span class="material-symbols-outlined text-lg">person_add</span>\n<span>Nuevo Cliente</span>\n</button>'
)

# Fix Funnel Title Typo ("Clientees")
html = html.replace('>Retención de Clientees</h3>', '>Embudo de Fidelización</h3>')

# Rename Funnel Bottom KPIs
html = html.replace('>Valor Total</p>', '>Valor Cartera</p>')
html = html.replace('>Ciclo Prom.</p>', '>Interacción Prom.</p>')
html = html.replace('>Conversión</p>', '>Tasa de Retención</p>')

# Replace the specific "Meta Trimestral" Card (div starting with <div class="bg-primary bg-gradient-to-br...)
# Up to </div></div></div>

new_kpi_card = """<!-- Small KPI Card -->
<div class="bg-primary bg-gradient-to-br from-primary to-primary-container p-6 rounded-xl text-on-primary flex flex-col justify-between">
<div>
<span class="material-symbols-outlined opacity-50 text-4xl mb-2" style="font-variation-settings: 'FILL' 1;">volunteer_activism</span>
<h3 class="text-sm font-medium opacity-80">Clientes Frecuentes</h3>
<p class="text-3xl font-black mt-1" id="kpiFrequentCount">0%</p>
</div>
<div class="mt-4">
<div class="w-full bg-surface/20 h-2 rounded-full overflow-hidden">
<div class="bg-surface h-full" id="kpiFrequentBar" style="width: 0%"></div>
</div>
<p class="text-[10px] mt-2 font-bold uppercase tracking-widest opacity-80" id="kpiFrequentSub">Base Total Activa</p>
</div>
</div>"""

html = re.sub(r'<!-- Small KPI Card -->\s*<div class="bg-primary bg-gradient-to-br from-primary to-primary-container.*?</p>\s*</div>\s*</div>\s*</div>', new_kpi_card, html, flags=re.DOTALL)


with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
