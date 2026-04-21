import re

path = r'd:\tesis\jhire\frontend\crm.html'

with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

new_lower_section = """<!-- Lower Section: Client Directory and AI Assistant -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    
    <!-- Client Directory Table (Left side - Main) -->
    <div class="lg:col-span-2 space-y-4">
        <div class="flex items-center justify-between">
            <h3 class="font-bold text-lg text-primary">Directorio de Clientes</h3>
            <button class="bg-primary/10 text-primary text-xs font-bold px-3 py-1.5 rounded-lg hover:bg-primary/20 transition-colors">Exportar CSV</button>
        </div>
        
        <div class="overflow-x-auto rounded-xl bg-surface-container-lowest border border-outline-variant/20 shadow-sm">
            <table class="w-full text-left border-collapse min-w-full">
                <thead>
                    <tr class="bg-surface-container-low">
                        <th class="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-on-surface-variant">Cliente</th>
                        <th class="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-on-surface-variant">Contacto</th>
                        <th class="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-on-surface-variant">Info Empresa</th>
                        <th class="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-on-surface-variant text-center">Interacciones</th>
                        <th class="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-on-surface-variant text-right">Acciones</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-outline-variant/10" id="crmClientsTableBody">
                    <tr><td colspan="5" class="p-6 text-center text-xs text-outline-variant">Cargando directorio de la Base de Datos...</td></tr>
                </tbody>
            </table>
            <div class="px-6 py-4 bg-surface-container-low flex items-center justify-between border-t border-outline-variant/10">
                <span class="text-xs text-on-surface-variant flex items-center gap-1"><span class="material-symbols-outlined text-sm text-green-500">check_circle</span> Directorio centralizado sincronizado</span>
            </div>
        </div>
    </div>
    
    <!-- AI Assistant Panel (Right side) -->
    <div class="lg:col-span-1 space-y-4">
        <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded bg-primary/10 text-primary flex items-center justify-center">
                <span class="material-symbols-outlined text-[18px]">psychology</span>
            </div>
            <h3 class="font-bold text-lg text-primary">AI Insights</h3>
        </div>
        <div class="bg-surface-container-lowest p-6 rounded-xl shadow-sm border border-outline-variant/20 min-h-[400px] flex flex-col relative overflow-hidden" id="crmAiAssistantContainer">
            <!-- decorative background -->
            <div class="absolute right-0 top-0 w-32 h-32 bg-primary/5 rounded-bl-full -z-0"></div>
            
            <!-- Empty State -->
            <div id="crmAiEmptyState" class="flex-1 flex flex-col items-center justify-center text-center opacity-70 relative z-10">
                <span class="material-symbols-outlined text-5xl text-outline mb-4" style="font-variation-settings: 'FILL' 0, 'wght' 200;">person_search</span>
                <p class="text-sm font-medium text-on-surface-variant max-w-[200px]">Selecciona un cliente de la tabla para que la IA escanee su LTV y brinde sugerencias comunicativas.</p>
            </div>
            
            <!-- Loading State -->
            <div id="crmAiLoading" class="flex-1 flex flex-col items-center justify-center hidden relative z-10">
                <div class="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                <p class="mt-4 text-xs font-bold text-primary animate-pulse">Analizando métricas cognitivas...</p>
            </div>
            
            <!-- Results State -->
            <div id="crmAiResults" class="hidden flex-col gap-5 h-full relative z-10 w-full">
                <div class="pb-4 border-b border-outline-variant/20">
                    <div class="flex items-start justify-between">
                        <div>
                            <h4 id="aiClientName" class="font-bold text-on-surface">Nombre Cliente</h4>
                            <p id="aiClientStatus" class="inline-flex mt-2 items-center px-2 py-0.5 rounded text-[10px] font-bold bg-primary/10 text-primary uppercase">Status</p>
                        </div>
                        <div class="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center text-primary shrink-0">
                            <span class="material-symbols-outlined text-xl">robot_2</span>
                        </div>
                    </div>
                </div>
                
                <div class="flex-1">
                    <h5 class="text-[10px] font-black uppercase tracking-widest text-outline mb-4 flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> Sugerencias Aprobadas</h5>
                    <ul id="aiRecommendationsList" class="space-y-4">
                        <!-- Items rendered dynamically -->
                    </ul>
                </div>
                
                <div class="mt-auto pt-4 flex gap-2">
                    <button onclick="Swal.fire('¡Campaña Enviada!','Se ha enviado la comunicación automatizada al cliente.','success')" class="flex-1 py-2.5 bg-primary text-white rounded-lg text-xs font-bold shadow hover:bg-primary/90 flex items-center justify-center gap-2 transition-colors active:scale-95">
                        <span class="material-symbols-outlined text-[16px]">campaign</span> Despachar Acción
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>"""

# Ensure we replace exactly the block starting from <!-- Lower Section: Products and Activities -->
# up to <!-- Intelligence Banner --> (exclusive, or including it? Let's just include Intelligence Banner as part of the overall logic that gets removed or kept.)
# Wait, crm.html has <!-- Intelligence Banner --> next. That is fine, we can keep it or delete it. The user actually said "y elimina ese icono de chatbot, no debe estar en esa pantalla y explicame como funciona el embudo". The user previously talked about "Intelligence Banner" in Ventas POS. In CRM maybe they like it. We'll leave it as is if it's there, but we replace the exact grid grid-cols-1 lg:grid-cols-3.

html = re.sub(r'<!-- Lower Section: Products and Activities -->\s*<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">.*?</div>\s*</div>\s*</div>\s*(?=<!-- Intelligence Banner -->)', new_lower_section + '\n', html, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated crm.html inner HTML layout.")
