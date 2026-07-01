import glob
import os

files = glob.glob('d:/tesis/jhire/frontend/*.html')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 1. Renombrar en el sidebar
    content = content.replace('Tiempo Facturación</', 'Tiempo de Procesamiento</')
    content = content.replace('Tiempo Facturación\n', 'Tiempo de Procesamiento\n')
    # Manejar caso con espacios extra si existiera
    content = content.replace('Tiempo Facturación<', 'Tiempo de Procesamiento<')
    
    # 2. Renombrar en tiempo_facturacion.html title tag y encabezados
    if 'tiempo_facturacion.html' in f:
        content = content.replace('<title>JHIRE 2026 - Tiempo Facturación</title>', '<title>JHIRE 2026 - Tiempo de Procesamiento</title>')
        content = content.replace('<h2 class="text-2xl font-headline font-black tracking-tighter">Tiempo Facturación</h2>', '<h2 class="text-2xl font-headline font-black tracking-tighter">Tiempo de Procesamiento de Facturas</h2>')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print(f"Renombrado completado en {len(files)} archivos.")
