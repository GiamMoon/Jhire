import os
import glob
import re

css_vars_block = """    <script id="tailwind-config">
          tailwind.config = {
            darkMode: "class",
            theme: {
              extend: {
                colors: {
                  "primary": "var(--color-primary)",
                  "surface": "var(--color-surface)",
                  "on-surface": "var(--color-on-surface)",
                  "surface-container": "var(--color-surface-container)",
                  "surface-container-low": "var(--color-surface-container-low)",
                  "surface-container-high": "var(--color-surface-container-high)",
                  "surface-container-highest": "var(--color-surface-container-highest)",
                  "outline": "var(--color-outline)",
                  "outline-variant": "var(--color-outline-variant)",
                  "error": "var(--color-error)",
                  "on-error": "var(--color-on-error)"
                },
                fontFamily: {
                  "headline": ["Manrope"],
                  "body": ["Inter"]
                }
              }
            }
          }
    </script>
    <style id="dynamic-theme">
        :root {
          --color-primary: #003461;
          --color-surface: #faf8ff;
          --color-on-surface: #131b2e;
          --color-surface-container: #eaedff;
          --color-surface-container-low: #f2f4ff;
          --color-surface-container-high: #d9e2ff;
          --color-surface-container-highest: #c5d2ff;
          --color-outline: #727781;
          --color-outline-variant: #c2c7d1;
          --color-error: #ba1a1a;
          --color-on-error: #ffffff;
        }

        html.dark {
          --color-primary: #a6c8ff;
          --color-surface: #111318;
          --color-on-surface: #e2e2e9;
          --color-surface-container: #1d2024;
          --color-surface-container-low: #191b20;
          --color-surface-container-high: #282a2f;
          --color-surface-container-highest: #33353a;
          --color-outline: #8c9199;
          --color-outline-variant: #42474e;
          --color-error: #ffb4ab;
          --color-on-error: #690005;
        }
    </style>"""

mobile_menu_html = """
<!-- Mobile Offcanvas Menu -->
<div id="mobileMenuOverlay" class="fixed inset-0 bg-black/50 z-[60] backdrop-blur-sm hidden transition-opacity opacity-0"></div>
<aside id="mobileMenuSidebar" class="fixed top-0 right-0 h-full w-72 bg-surface shadow-2xl z-[70] transform translate-x-full transition-transform duration-300 flex flex-col">
    <div class="h-20 flex items-center justify-between px-6 border-b border-outline/10">
        <span class="font-black text-primary tracking-widest uppercase text-sm">Menú</span>
        <button id="closeMobileMenuBtn" class="w-10 h-10 flex items-center justify-center rounded-full bg-surface-container-low hover:bg-surface-container transition-colors text-on-surface">
            <span class="material-symbols-outlined text-lg">close</span>
        </button>
    </div>
    <div class="flex flex-col p-6 gap-6 flex-1 overflow-y-auto">
        <a href="inicio.html" class="flex items-center gap-4 text-base font-bold text-on-surface hover:text-primary transition-colors"><span class="material-symbols-outlined">home</span> Inicio</a>
        <a href="catalogo_usuario.html" class="flex items-center gap-4 text-base font-bold text-on-surface hover:text-primary transition-colors"><span class="material-symbols-outlined">inventory_2</span> Catálogo</a>
        <a href="mis_pedidos.html" class="flex items-center gap-4 text-base font-bold text-on-surface hover:text-primary transition-colors"><span class="material-symbols-outlined">receipt_long</span> Mis Pedidos</a>
        <hr class="border-outline/10">
        <a href="perfil_usuario.html" class="flex items-center gap-4 text-base font-bold text-on-surface hover:text-primary transition-colors"><span class="material-symbols-outlined">account_circle</span> Mi Perfil</a>
    </div>
</aside>
"""

frontend_path = r"d:\tesis\jhire\frontend\*.html"
for filepath in glob.glob(frontend_path):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace tailwind config script
    pattern_tailwind = re.compile(r'<script id="tailwind-config">.*?</script>', re.DOTALL)
    if not '<style id="dynamic-theme">' in content:
        content = pattern_tailwind.sub(css_vars_block, content)
    
    # 2. Append mobile offcanvas just before </body>
    if 'id="mobileMenuOverlay"' not in content:
        content = content.replace('</body>', mobile_menu_html + '\n</body>')
        
    # 3. Add Hamburger button to nav if missing
    # I find the wrapper where the avatar is to insert the hamburger button
    # Let's cleanly inject it right before the avatar container using Regex or string find
    # The container wrapper starts with `<div class="flex items-center gap-6 relative">`
    ham_btn = '<button id="openMobileMenuBtn" class="md:hidden flex items-center justify-center w-10 h-10 rounded-full border border-outline-variant/30 text-on-surface bg-surface hover:bg-surface-container transition-colors mr-2"><span class="material-symbols-outlined">menu</span></button>'
    if 'id="openMobileMenuBtn"' not in content:
        # We find: `<div class="flex items-center gap-6 relative">`
        # and replace with it + the button.
        content = content.replace('<div class="flex items-center gap-6 relative">', f'<div class="flex items-center gap-6 relative">\n        {ham_btn}')
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Patch applied to all HTML files successfully.")
