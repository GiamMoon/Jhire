import re, glob

# The exact new right side of the app bar:
new_right = """<div class="flex items-center gap-4">
            <button onclick="changeTheme(document.documentElement.classList.contains('dark') ? 'light' : 'dark')" class="w-10 h-10 rounded-full border border-outline-variant/30 hover:bg-surface-container transition-colors flex items-center justify-center text-on-surface">
                <span class="material-symbols-outlined text-[20px]" id="themeIcon">dark_mode</span>
            </button>
            <button class="w-10 h-10 rounded-full border border-outline-variant/30 hover:bg-surface-container transition-colors flex items-center justify-center text-on-surface relative">
                <span class="material-symbols-outlined text-[20px]">notifications</span>
                <span class="absolute top-2 right-2 w-2 h-2 bg-error rounded-full border-2 border-surface"></span>
            </button>
            <div class="flex items-center gap-3 bg-surface-container-low pl-1 pr-3 py-1 rounded-full border border-outline-variant/20 shadow-sm cursor-pointer hover:shadow-md transition-all" id="avatarContainer">
                <img id="userAvatar" src="https://ui-avatars.com/api/?name=Admin+Root&background=003461&color=fff" class="w-8 h-8 rounded-full border-2 border-primary/20">
                <div class="hidden md:block text-left relative top-[1px]">
                    <p id="headerUserName" class="text-[11px] font-black text-on-surface uppercase tracking-wide leading-none">Cargando...</p>
                    <p id="headerUserRole" class="text-[9px] text-primary font-bold uppercase tracking-widest leading-none mt-[2px]">...</p>
                </div>
            </div>
        </div>"""

files = glob.glob(r'd:\tesis\jhire\frontend\*.html')
for fn in files:
    # Only target admin dashboard pages that have a <header>
    # We will target the second <div class="flex items-center gap-4"> inside <header
    with open(fn, 'r', encoding='utf-8') as f:
        html = f.read()
    
    if '<header' in html and 'notifications' in html and 'ui-avatars.com' in html:
        # We replace the specific block.
        # Find the block starting with <div class="flex items-center gap-4"> that contains notifications
        html = re.sub(r'<div class="flex items-center gap-4">\s*<button class="w-10 h-10 rounded-full border[^>]*>.*?<span class="material-symbols-outlined[^>]*>notifications.*?</div>\s*</div>', new_right, html, flags=re.DOTALL)
        
        # Also, check if <html class="light"> needs to be <html class="light " id="html-root">? 
        # App.js doesn't specifically need an ID, it targets document.documentElement!
        
        with open(fn, 'w', encoding='utf-8') as f:
            f.write(html)
        print("Updated Appbar in", fn)
