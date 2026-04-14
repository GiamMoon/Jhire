import os
import re
import glob

# The new footer to replace whatever was there
new_footer = """<footer class="bg-on-surface text-surface py-16 border-t border-outline/10 mt-auto">
    <div class="max-w-7xl mx-auto px-8 grid grid-cols-1 md:grid-cols-4 gap-12 text-sm">
        <div class="md:col-span-1">
            <div class="text-2xl font-black mb-4 text-on-primary-container">JHIRE</div>
            <p class="text-surface-container/60 mb-6 leading-relaxed">Su aliado estratégico en suministros industriales de limpieza. Liderando el sector operativo 2026.</p>
        </div>
        <div>
            <h4 class="font-bold text-lg mb-4 text-white">Empresa</h4>
            <ul class="space-y-3 text-surface-container/60">
                <li><a href="sobre_nosotros.html" class="hover:text-primary transition-colors">Sobre Nosotros</a></li>
                <li><a href="contacto_comercial.html" class="hover:text-primary transition-colors">Contacto Comercial</a></li>
            </ul>
        </div>
        <div>
            <h4 class="font-bold text-lg mb-4 text-white">Legal</h4>
            <ul class="space-y-3 text-surface-container/60">
                <li><a href="politica_privacidad.html" class="hover:text-primary transition-colors">Política de Privacidad</a></li>
                <li><a href="terminos_condiciones.html" class="hover:text-primary transition-colors">Términos y Condiciones</a></li>
            </ul>
        </div>
        <div>
            <h4 class="font-bold text-lg mb-4 text-white">Redes y Contacto</h4>
            <ul class="space-y-3 text-surface-container/60 flex flex-col">
                <li><a href="https://wa.me/51970801549" target="_blank" class="hover:text-primary transition-colors flex items-center gap-2"><span class="material-symbols-outlined text-lg">chat</span> WhatsApp: +51 970 801 549</a></li>
            </ul>
        </div>
    </div>
    <div class="max-w-7xl mx-auto px-8 mt-12 pt-8 border-t border-white/10 text-center text-surface-container/40">
        <p>© 2026 JHIRE. Todos los derechos reservados.</p>
    </div>
</footer>"""

footer_pattern = re.compile(r'<footer\b[^>]*>.*?</footer>', re.DOTALL | re.IGNORECASE)

html_files = glob.glob(r'd:\tesis\jhire\frontend\*.html')

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace footer
    if footer_pattern.search(content):
        content = footer_pattern.sub(new_footer, content)
    else:
        # If no footer, insert before </body> or at end
        body_end = content.find('</body')
        if body_end != -1:
            content = content[:body_end] + new_footer + '\n' + content[body_end:]
        else:
            content += '\n' + new_footer

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
print("Updated all HTML files with new footer.")
