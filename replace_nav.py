import glob
import re

new_nav = """<nav class="fixed top-0 right-0 w-full z-50 bg-surface/80 backdrop-blur-xl border-b border-white/20 shadow-sm flex justify-between items-center h-20 px-6 md:px-12 transition-all duration-300">
    <div class="flex items-center gap-10">
        <div class="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity" onclick="window.location.href='inicio.html'">
             <span class="material-symbols-outlined text-primary text-3xl" style="font-variation-settings: 'FILL' 1;">precision_manufacturing</span>
             <span class="text-2xl font-black tracking-tighter text-primary bg-clip-text">JHIRE</span>
        </div>
        <div class="hidden md:flex gap-8 items-center mt-1">
            <a class="relative text-on-surface hover:text-primary font-bold text-[13px] tracking-wider uppercase transition-all duration-300" href="inicio.html">Inicio</a>
            <a class="relative text-on-surface hover:text-primary font-bold text-[13px] tracking-wider uppercase transition-all duration-300" href="catalogo_usuario.html">Catálogo</a>
            <a class="relative text-on-surface hover:text-primary font-bold text-[13px] tracking-wider uppercase transition-all duration-300" href="mis_pedidos.html">Mis Pedidos</a>
        </div>
    </div>
    <div class="flex items-center gap-6 relative">
        <div class="flex items-center gap-4 relative">
            <span id="headerUserName" class="font-bold text-sm hidden sm:inline-block">Cargando...</span>
            <div id="avatarContainer" class="w-10 h-10 rounded-full bg-surface-container overflow-hidden border-2 border-primary/20 cursor-pointer hover:ring-4 ring-primary/10 transition-all shadow-sm">
                <img id="userAvatar" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBSiDqfnMrirjJLlMScM4CkdykZ97ca7BS5Gs2ZYAU056Yp6tuX6bY_v_0gZxiBV2e_CaeLVJ2FrBk_GxJFpbfeZUOYKMlYaV4OYNcM2H3eGhEKeSXB5W4QpHGHRyQCJo8w1HlpoFd1SZCvRHQdRoth2N4HP6fQydTFOG456as-FQdLVktIZ8KcqBXqAbxnQl5VofUz1WPiYTnDf-d5wU395DOKpkAL7pmc-cQhDjakfy6FmMLz0Zhv-VWHAiPpGiB6OFz79UTkaP_7" alt="User" class="w-full h-full object-cover">
            </div>
            <!-- Logout Dropdown -->
            <div id="logoutDropdown" class="absolute top-12 right-0 bg-white shadow-2xl border border-outline/10 rounded-xl py-2 w-48 hidden z-50">
                <button id="logoutBtn" class="w-full text-left px-5 py-3 text-sm text-error hover:bg-error/5 font-bold flex items-center gap-3 transition-colors">
                    <span class="material-symbols-outlined text-[18px]">logout</span> Cerrar Sesión
                </button>
            </div>
        </div>
    </div>
</nav>"""

def replace_navs():
    files = glob.glob('frontend/*.html')
    # Filter out login.html as it might not have nav
    for f in files:
        if 'login.html' in f:
            continue
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Regex to find the <nav... > ... </nav>
        pattern = re.compile(r'<nav[^>]*>.*?</nav>', re.DOTALL)
        
        if pattern.search(content):
            content = pattern.sub(new_nav, content)
            
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f'Nav replaced in {f}')
        else:
            print(f'No nav found in {f}')

replace_navs()
