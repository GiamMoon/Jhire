import os
import glob
import re

frontend_path = r"d:\tesis\jhire\frontend\*.html"
filepaths = glob.glob(frontend_path)

for filepath in filepaths:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Fix body tag to ALWAYS be bg-surface and flex layout (pushes footer down)
    content = re.sub(r'<body class="([^"]*)">', r'<body class="\1 flex flex-col min-h-screen">', content)
    content = content.replace('bg-background', 'bg-surface')

    # 2. Fix the Footer classes
    # Some files had bg-on-surface text-surface. Replace with concrete hex colors that support dark mode elegantly
    new_footer = '<footer class="bg-[#0b1829] text-[#e2e2e9] py-16 border-t border-white/10 mt-auto dark:bg-[#05090e]">'
    content = re.sub(r'<footer class="[^"]*">', new_footer, content)

    # 3. Filter buttons in Catalog were completely black in some cases because of text-on-primary
    content = content.replace('bg-primary text-on-primary', 'bg-primary text-white')
    content = content.replace('text-on-surface-variant hover:bg-surface-container', 'text-on-surface hover:bg-surface-container-high dark:hover:bg-surface-container')

    # 4. Save
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("HTML repairs completed.")
