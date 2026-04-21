import re

path = r'd:\tesis\jhire\frontend\app.js'
with open(path, 'r', encoding='utf-8') as f:
    js = f.read()

new_crm_logic = """    // --- LÓGICA CRM DINÁMICA ---
    const loadDynamicCRM = async () => {
        const token = localStorage.getItem('jhire_jwt_token');
        let clientsData = [];
        
        const crmClientsTableBody = document.getElementById('crmClientsTableBody');
        if (crmClientsTableBody) {
            try {
                const res = await fetch('http://localhost:8000/api/crm/clients', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const clients = await res.json();
                    clientsData = clients;
                    if(clients.length > 0) {
                        crmClientsTableBody.innerHTML = clients.map(client => `
                            <tr class="hover:bg-surface-container-high transition-colors bg-surface dark:bg-surface-container cursor-pointer" onclick="analyzeCRMProfile(${client.id}, '${client.name}')">
                                <td class="px-6 py-4">
                                    <div class="flex items-center gap-3">
                                        <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(client.name)}&background=random" class="w-8 h-8 rounded-full border border-outline-variant/30">
                                        <div>
                                            <p class="text-xs font-bold text-on-surface">${client.name}</p>
                                            <p class="text-[10px] text-on-surface-variant">ID: #${client.id}</p>
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4">
                                    <p class="text-xs font-medium text-slate-500 flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">mail</span> ${client.email}</p>
                                    <p class="text-[10px] text-slate-500 mt-1 flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">call</span> ${client.phone || 'No registrado'}</p>
                                </td>
                                <td class="px-6 py-4">
                                    <p class="text-xs font-bold">${client.company}</p>
                                    <p class="text-[10px] text-on-surface-variant">RUC/DNI: ${client.ruc_dni}</p>
                                </td>
                                <td class="px-6 py-4 text-center">
                                    <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-tertiary-container/30 text-tertiary-container font-bold text-[10px]">
                                        ${client.interactions_count}
                                    </span>
                                </td>
                                <td class="px-6 py-4 text-right">
                                    <div class="flex justify-end gap-2">
                                        <button onclick="event.stopPropagation(); window.open('mailto:${client.email}')" class="py-1 px-2.5 bg-surface-container hover:bg-primary/10 hover:text-primary rounded text-on-surface text-[10px] font-bold flex items-center gap-1 transition-colors border border-outline-variant/30">
                                            <span class="material-symbols-outlined text-[14px]">mail</span> Mensaje
                                        </button>
                                        <button onclick="event.stopPropagation(); window.open('https://wa.me/${client.phone ? client.phone.replace(/\\D/g,'') : ''}')" class="py-1 px-2.5 bg-surface-container hover:bg-green-100 hover:text-green-700 rounded text-on-surface text-[10px] font-bold flex items-center gap-1 transition-colors border border-outline-variant/30">
                                            <span class="material-symbols-outlined text-[14px]">chat</span> WhatsApp
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('');
                    } else {
                        crmClientsTableBody.innerHTML = '<tr><td colspan="5" class="p-6 text-center text-xs text-outline-variant">Aún no hay clientes registrados en la BD.</td></tr>';
                    }
                }
            } catch(e) {
                console.error('Error fetching CRM clients:', e);
            }
        }
        
        // Re-use clients endpoint to dynamically calculate REAL CRM KPIs
        const crmFunnelContainer = document.getElementById('crmFunnelContainer');
        if (crmFunnelContainer && clientsData) {
            try {
                // Generate funnel data based on clients real interactions
                const totalClients = clientsData.length;
                const contactados = clientsData.filter(c => c.interactions_count >= 1).length;
                const enProceso = clientsData.filter(c => c.interactions_count >= 3).length;
                const fidelizados = clientsData.filter(c => c.interactions_count >= 6).length;
                
                crmFunnelContainer.innerHTML = `
                    <div class="funnel-step flex-1 bg-primary flex flex-col items-center justify-center text-on-primary relative">
                        <span class="text-2xl font-black">${totalClients}</span><span class="text-[10px] font-bold uppercase tracking-wider opacity-80">Registrados</span>
                    </div>
                    <div class="funnel-step flex-1 bg-primary/85 flex flex-col items-center justify-center text-on-primary">
                        <span class="text-2xl font-black">${contactados}</span><span class="text-[10px] font-bold uppercase tracking-wider opacity-80">Contactados</span>
                    </div>
                    <div class="funnel-step flex-1 bg-primary/70 flex flex-col items-center justify-center text-on-primary">
                        <span class="text-2xl font-black">${enProceso}</span><span class="text-[10px] font-bold uppercase tracking-wider opacity-80">Activos</span>
                    </div>
                    <div class="funnel-step flex-1 bg-primary/55 flex flex-col items-center justify-center text-on-primary">
                        <span class="text-2xl font-black">${fidelizados}</span><span class="text-[10px] font-bold uppercase tracking-wider opacity-80">Fidelizados</span>
                    </div>
                `;
                
                const kpiValorTotal = document.getElementById('kpiValorTotal');
                const kpiCicloProm = document.getElementById('kpiCicloProm');
                const kpiConversion = document.getElementById('kpiConversion');
                
                if (kpiValorTotal) {
                    const totalInteracciones = clientsData.reduce((sum, c) => sum + c.interactions_count, 0);
                    kpiValorTotal.innerText = totalInteracciones.toString() + ' Puntos';
                }
                if(kpiCicloProm) {
                    const promResult = totalClients > 0 ? (clientsData.reduce((sum, c) => sum + c.interactions_count, 0) / totalClients).toFixed(1) : 0;
                    kpiCicloProm.innerText = promResult;
                }
                if(kpiConversion) {
                    const retentionRate = totalClients > 0 ? (contactados / totalClients) * 100 : 0;
                    kpiConversion.innerText = retentionRate.toFixed(1) + '%';
                }
                
                // Small KPI Card - Frequent Clients
                const kpiFrequentCount = document.getElementById('kpiFrequentCount');
                const kpiFrequentBar = document.getElementById('kpiFrequentBar');
                if(kpiFrequentCount && kpiFrequentBar) {
                    const freqRate = totalClients > 0 ? (fidelizados / totalClients) * 100 : 0;
                    kpiFrequentCount.innerText = freqRate.toFixed(1) + '%';
                    kpiFrequentBar.style.width = freqRate + '%';
                }
                
            } catch(e) {
                console.error("Funnel processing error:", e);
            }
        }
    };"""

js = re.sub(r'// --- LÓGICA CRM DINÁMICA ---.*?// --- LÓGICA FACTURACIÓN DINÁMICA ---', 
            lambda m: new_crm_logic + '\n\n    // --- LÓGICA FACTURACIÓN DINÁMICA ---', 
            js, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated app.js logic for CRM Funnel and Buttons successfully.")
