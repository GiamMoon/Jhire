import re

# 1. Read crm.html
path = r'd:\tesis\jhire\frontend\crm.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 2. Fix missing </div> closing the Bento Grid
html = html.replace('<!-- Lower Section: Client Directory and AI Assistant -->', 
                    '</div>\n<!-- Lower Section: Client Directory and AI Assistant -->')

# 3. Change "Ventas & Prospecting" header text
html = html.replace('<h2 class="text-3xl font-extrabold text-primary tracking-tight">Ventas &amp; Prospecting</h2>', 
                    '<h2 class="text-3xl font-extrabold text-primary tracking-tight">Gestión CRM Central</h2>')

# Write back
with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
