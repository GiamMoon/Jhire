import glob

def inject_sweetalert():
    files = glob.glob('frontend/*.html')
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if 'sweetalert2' not in content:
            content = content.replace('</head>', '    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>\n</head>')
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f'Injected in {f}')

inject_sweetalert()
