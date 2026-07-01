import os
import glob

html_files = glob.glob("d:/tesis/jhire/frontend/*.html")

search_block = """        <a href="tiempo_ventas.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">speed</span> Eficiencia Ventas
        </a>"""

search_block_active = """        <a href="tiempo_ventas.html" class="flex items-center gap-3 px-4 py-3 bg-primary/10 text-primary font-bold rounded-xl shadow-sm transition-colors">
            <span class="material-symbols-outlined">speed</span> Eficiencia Ventas
        </a>"""

insert_block = """
        <a href="tiempo_facturacion.html" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-bold rounded-xl transition-colors">
            <span class="material-symbols-outlined">receipt_long</span> Tiempo Facturación
        </a>"""

for file_path in html_files:
    if "tiempo_facturacion.html" in file_path:
        continue # skip itself just in case
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "tiempo_facturacion.html" not in content and "tiempo_ventas.html" in content:
        if search_block in content:
            new_content = content.replace(search_block, search_block + insert_block)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated {file_path}")
        elif search_block_active in content:
            new_content = content.replace(search_block_active, search_block_active + insert_block)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated {file_path}")
