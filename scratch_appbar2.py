import re
import glob

new_right = """<div class="flex items-center gap-4">
            <!-- Theme Toggle -->
            <button onclick="changeTheme(document.documentElement.classList.contains('dark') ? 'light' : 'dark')" class="w-10 h-10 rounded-full border border-outline-variant/30 hover:bg-surface-container transition-colors flex items-center justify-center text-on-surface">
                <span class="material-symbols-outlined text-[20px]" id="themeIcon">dark_mode</span>
            </button>
            <button class="w-10 h-10 rounded-full border border-outline-variant/30 hover:bg-surface-container transition-colors flex items-center justify-center text-on-surface relative">
                <span class="material-symbols-outlined text-[20px]">notifications</span>
                <span class="absolute top-2 right-2 w-2 h-2 bg-error rounded-full border-2 border-surface"></span>
            </button>
            <div class="flex items-center gap-3 bg-surface-container-low pl-1 pr-3 py-1 rounded-full border border-outline-variant/20 shadow-sm cursor-pointer hover:shadow-md transition-all" id="avatarContainer">
                <img id="userAvatar" src="https://ui-avatars.com/api/?name=User&background=003461&color=fff" class="w-8 h-8 rounded-full border-2 border-primary/20">
                <div class="hidden md:block text-left relative top-[1px]">
                    <p id="headerUserName" class="text-[11px] font-black text-on-surface uppercase tracking-wide leading-none">Cargando...</p>
                    <p id="headerUserRole" class="text-[9px] text-primary font-bold uppercase tracking-widest leading-none mt-[2px]">...</p>
                </div>
            </div>
        </div>
    </header>"""

# Using python to load HTML, split at </header>, grab the text before </header>, and string replace the last "<div class='flex items-center gap-4'>" block.
files = glob.glob(r'd:\tesis\jhire\frontend\*.html')
for fn in files:
    with open(fn, 'r', encoding='utf-8') as f:
        html = f.read()

    if '</header>' in html and 'gap-4' in html:
        parts = html.split('</header>')
        header_content = parts[0]
        
        # find the last occurrence of '<div class="flex items-center gap-4">' inside header_content
        last_idx = header_content.rfind('<div class="flex items-center gap-4">')
        if last_idx != -1:
            header_content = header_content[:last_idx] + new_right
            html = header_content + '</header>'.join(parts[1:])
            
            with open(fn, 'w', encoding='utf-8') as f:
                f.write(html)
            print("Successfully updated top app bar in", fn)
