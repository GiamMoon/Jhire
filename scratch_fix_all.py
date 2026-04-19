import re
import os

files = ['crm.html', 'ventas.html', 'facturacion.html']

for fn in files:
    path = os.path.join(r'd:\tesis\jhire\frontend', fn)
    if not os.path.exists(path): continue
    
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
        
    # Remove footer entirely
    html = re.sub(r'<footer.*?</footer>', '', html, flags=re.DOTALL)
    
    # Text replacements for remaining English
    html = html.replace('Historical data suggests an increase in demand for <span class="font-bold text-primary">Synthetic Nylon Brushes</span> in the textile sector over the next 15 days. We recommend proactive outreach to Top 5 clients.', 'Los datos históricos sugieren un aumento en la demanda en el sector industrial durante los próximos 15 días. Recomendamos envío de promos masivas a los Top 5 clientes.')
    html = html.replace('Historical data suggests an increase in demand for <span class="font-bold text-primary">Synthetic Nylon Brushes</span> in the textile sector over the next 15 days.', 'Los datos históricos sugieren un aumento en la demanda en el sector industrial durante los próximos 15 días.')
    html = html.replace('Historical data suggests an increase in demand for Synthetic Nylon Brushes in the textile sector over the next 15 days. We recommend proactive outreach to Top 5 clients.', 'Los datos históricos sugieren un aumento en la demanda en el sector. Recomendamos accion proactiva.')
    html = html.replace('Showing 4 of 128 transactions', 'Mostrando transacciones recientes de Base de Datos')
    html = html.replace('Run Campaign', 'Desplegar Campaña')
    
    # In case any other stray english strings didn't get caught
    html = html.replace('Showing 4 of', 'Mostrando últimas')
    html = html.replace('transactions', 'transacciones')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
        
print("HTML static fixes applied.")

# Now fix app.js dark mode colors where injected JS is used
app_js_path = r'd:\tesis\jhire\frontend\app.js'
with open(app_js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Replace bad hardcoded Tailwind colors that break dark mode
js = js.replace('hover:bg-slate-50', 'hover:bg-surface-container-high transition-colors')
js = js.replace('bg-surface-container-lowest', 'bg-surface dark:bg-surface-container')
js = js.replace('border-slate-50', 'border-outline-variant/20')

with open(app_js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("JS dark mode fixes applied.")
