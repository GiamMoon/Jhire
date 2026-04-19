import re

path = r'd:\tesis\jhire\frontend\ventas.html'

with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# Fix Meta Trimestral Card styling for contrast
html = html.replace('class="bg-primary bg-gradient-to-br from-primary to-primary-container p-6 rounded-xl text-on-primary flex flex-col justify-between"', 'class="bg-primary bg-gradient-to-br from-primary to-primary-container p-6 rounded-xl text-white flex flex-col justify-between"')

# Find Filtros Button:
# <button class="flex items-center gap-2 px-4 py-2.5 bg-surface-container-low text-primary font-semibold rounded-md hover:bg-surface-container-high transition-colors">
# <span class="material-symbols-outlined text-lg">filter_list</span>
# <span>Filtros</span>
# </button>
html = html.replace('class="flex items-center gap-2 px-4 py-2.5 bg-surface-container-low text-primary font-semibold rounded-md hover:bg-surface-container-high transition-colors"\n>\n<span class="material-symbols-outlined text-lg">filter_list</span>', 'class="flex items-center gap-2 px-4 py-2.5 bg-surface-container-low text-primary font-semibold rounded-md hover:bg-surface-container-high transition-colors" onclick="Swal.fire(\'Filtros Avanzados\', \'El módulo de filtros comerciales estará conectado al CRM en la v2.0\', \'info\')">\n<span class="material-symbols-outlined text-lg">filter_list</span>')
# In case line breaks differ:
html = re.sub(r'<button class="([^"]*?)">(\s*<span class="material-symbols-outlined[^>]*>filter_list</span>\s*<span>Filtros</span>\s*)</button>', r'<button class="\1" onclick="Swal.fire(\'Filtros Avanzados\', \'El módulo de filtros comerciales se activará en la etapa v2.0\', \'info\')">\2</button>', html, flags=re.DOTALL)


# Find Nueva Venta Rapida
# <button class="flex items-center gap-2 px-6 py-2.5 bg-primary text-white font-bold rounded-md shadow-lg shadow-primary/20 active:scale-95 transition-all">
# <span class="material-symbols-outlined text-lg">add_shopping_cart</span>
# <span>Nueva Venta Rápida</span>
# </button>
html = re.sub(r'<button class="([^"]*?)">(\s*<span class="material-symbols-outlined[^>]*>add_shopping_cart</span>\s*<span>Nueva Venta Rápida</span>\s*)</button>', r'<button class="\1" onclick="location.href=\'admin_catalogo.html\'">\2</button>', html, flags=re.DOTALL)


# Find Ver Todo
# <button class="text-primary text-xs font-bold hover:underline">Ver Todo</button>
html = html.replace('<button class="text-primary text-xs font-bold hover:underline">Ver Todo</button>', '<button class="text-primary text-xs font-bold hover:underline" onclick="location.href=\'admin_catalogo.html\'">Ver Todo</button>')


with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
