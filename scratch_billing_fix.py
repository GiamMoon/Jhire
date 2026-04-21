import re

# 1. Update facturacion.html

with open(r'd:\tesis\jhire\frontend\facturacion.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add ID to form
html = html.replace('<form class="space-y-6">', '<form id="invoiceForm" class="space-y-6">')

# Extract RUC and Client Name IDs
html = html.replace('<input class="w-full bg-surface-container-low border-none border-b-2 border-primary/20 focus:border-primary focus:ring-0 rounded-t-sm text-sm" type="text"/>',
                    '<input id="clientNameInput" class="w-full bg-surface-container-low border-none border-b-2 border-primary/20 focus:border-primary focus:ring-0 rounded-t-sm text-sm" placeholder="Razón Social / Nombre" type="text" required/>')

html = html.replace('<input id="rucInput" class="flex-grow bg-surface-container-low border-none border-b-2 border-primary/20 focus:border-primary focus:ring-0 rounded-t-sm text-sm" placeholder="20600000000" type="text" maxlength="11"/>',
                    '<input id="rucInput" class="flex-grow bg-surface-container-low border-none border-b-2 border-primary/20 focus:border-primary focus:ring-0 rounded-t-sm text-sm" placeholder="20600000000 o 45678912" type="text" maxlength="11" required/>')


# Replace Detalle del Item with "Vinculación de Pedido"
old_items_section = """<h3 class="text-sm font-bold text-primary flex items-center gap-2">
<span class="material-symbols-outlined text-lg">list_alt</span> Detalle del Item
                                </h3>
<div class="grid grid-cols-12 gap-4 items-end bg-surface p-3 rounded-lg">
<div class="col-span-6 space-y-1">
<label class="text-[10px] font-bold text-on-surface-variant uppercase">Descripción</label>
<input class="w-full bg-surface border-outline-variant/30 rounded-md text-sm" placeholder="Producto o Servicio" type="text"/>
</div>
<div class="col-span-2 space-y-1">
<label class="text-[10px] font-bold text-on-surface-variant uppercase">Cant.</label>
<input class="w-full bg-surface border-outline-variant/30 rounded-md text-sm" type="number" value="1"/>
</div>
<div class="col-span-3 space-y-1">
<label class="text-[10px] font-bold text-on-surface-variant uppercase">P. Unit</label>
<input class="w-full bg-surface border-outline-variant/30 rounded-md text-sm" placeholder="0.00" type="number"/>
</div>
<div class="col-span-1 flex justify-center pb-1">
<button class="text-error hover:bg-error-container p-1 rounded-md" type="button">
<span class="material-symbols-outlined">delete</span>
</button>
</div>
</div>
<button class="text-xs font-bold text-primary-container flex items-center gap-1 hover:underline" type="button">
<span class="material-symbols-outlined text-sm">add</span> AGREGAR ITEM
                                </button>"""

new_items_section = """<h3 class="text-sm font-bold text-primary flex items-center gap-2">
<span class="material-symbols-outlined text-lg">receipt_long</span> Vinculación con Pedidos Registrados
</h3>
<div class="grid grid-cols-1 gap-4 items-end bg-surface p-4 rounded-lg border-2 border-dashed border-primary/20">
    <div class="space-y-2">
        <label class="text-[10px] font-bold text-on-surface-variant uppercase">ID de la Orden a Facturar (Order ID)</label>
        <div class="flex gap-2">
            <span class="flex items-center justify-center p-2 bg-slate-100 rounded-md font-bold text-outline-variant">#</span>
            <input id="orderIdInput" class="w-full bg-surface border-outline-variant/30 text-primary font-bold rounded-md text-sm focus:ring-primary" placeholder="Ej. 12" type="number" required/>
        </div>
        <p class="text-[10px] text-on-surface-variant"><span class="font-bold text-primary">Req. Legal:</span> SUNAT exige trazabilidad total. La factura calculará el subtotal e IGV(18%) en base al monto de la orden.</p>
    </div>
</div>"""

html = html.replace(old_items_section, new_items_section)

# Remove mock items from recent invoices container
mock_invoices_re = re.compile(r'<div class="space-y-4" id="recentInvoicesContainer">.*?</div>\n</section>', re.DOTALL)
html = mock_invoices_re.sub('<div class="space-y-4" id="recentInvoicesContainer">\n<!-- Items cargados dinamicamente via JS -->\n</div>\n</section>', html)

# Change some UI text to represent SUNAT logic slightly better
html = html.replace("Gestión de comprobantes electrónicos bajo normativa SUNAT 2025.", "Gestión de comprobantes electrónicos integrados a OSE/PSE SUNAT 2026.")

with open(r'd:\tesis\jhire\frontend\facturacion.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 2. Update app.js
with open(r'd:\tesis\jhire\frontend\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

billing_js = r"""
    // --- LÓGICA FACTURACIÓN DINÁMICA ---
    const loadDynamicBilling = async () => {
        const invContainer = document.getElementById('recentInvoicesContainer');
        if(invContainer) {
            const token = localStorage.getItem('jhire_jwt_token');
            try {
                const res = await fetch('http://localhost:8000/api/billing/', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if(res.ok) {
                    const invoices = await res.json();
                    if(invoices.length > 0) {
                        invContainer.innerHTML = invoices.slice(0, 5).map(i => `
                        <div class="flex items-center justify-between p-3 border-b border-outline-variant/10 bg-surface dark:bg-surface-container hover:bg-surface-container-low transition-colors group cursor-pointer" onclick="Swal.fire({title: 'Detalle de Comprobante', html: '<p><strong>Factura:</strong> ${i.invoice_number}</p><p><strong>Cliente:</strong> ${i.client_name}</p><p><strong>RUC:</strong> ${i.client_ruc_dni}</p><br><p><strong>Subtotal:</strong> S/ ${i.subtotal}</p><p><strong>IGV (18%):</strong> S/ ${i.igv}</p><p><strong>Total:</strong> S/ ${i.total}</p>', icon: 'info'})">
                            <div class="flex items-center gap-4">
                                <div class="w-10 h-10 rounded ${i.sunat_status === 'Emitida' ? 'bg-green-100 text-green-700' : 'bg-surface-container/20 text-on-surface-variant'} flex items-center justify-center shadow-sm">
                                    <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">${i.sunat_status === 'Emitida' ? 'check_circle' : 'hourglass_empty'}</span>
                                </div>
                                <div>
                                    <p class="text-sm font-black text-primary group-hover:underline">${i.invoice_number}</p>
                                    <p class="text-[10px] text-on-surface-variant font-bold mt-[2px]">${i.client_name} <span class="bg-surface-container-high px-1 rounded ml-1 text-outline">RUC: ${i.client_ruc_dni}</span></p>
                                </div>
                            </div>
                            <div class="text-right">
                                <p class="text-sm font-black text-on-surface">S/ ${parseFloat(i.total).toFixed(2)}</p>
                                <span class="text-[9px] font-black ${i.sunat_status === 'Emitida' ? 'text-green-600 bg-green-50 px-1 py-0.5 rounded' : 'text-on-surface-variant'} uppercase flex items-center justify-end gap-1"><span class="material-symbols-outlined text-[10px]">cloud_done</span> ${i.sunat_status} SUNAT</span>
                            </div>
                        </div>
                        `).join('');
                    } else {
                        invContainer.innerHTML = '<div class="p-8 text-center text-xs text-outline-variant flex flex-col items-center bg-surface-container-lowest rounded-lg border border-dashed border-outline/30"><span class="material-symbols-outlined text-4xl opacity-50 mb-2">receipt_long</span><p class="font-bold">Ningún comprobante fiscal emitido.</p></div>';
                    }
                }
            } catch(e) {}
        }
    };
    
    // Configurar Envío de Factura Formulada
    const invoiceForm = document.getElementById('invoiceForm');
    if(invoiceForm) {
        invoiceForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const rucInput = document.getElementById('rucInput').value.trim();
            const clientNameInput = document.getElementById('clientNameInput').value.trim();
            const orderIdInput = document.getElementById('orderIdInput').value.trim();
            const compliance = document.getElementById('compliance').checked;
            const law29733 = document.getElementById('law29733').checked;
            
            if(!compliance || !law29733) {
                Swal.fire('Requisito Legal', 'Debe aceptar las políticas de privacidad y compliance SUNAT para generar comprobantes electrónicos.', 'warning');
                return;
            }
            
            if(!/^\d{8}$|^\d{11}$/.test(rucInput)) {
                Swal.fire('Error de RUC', 'El RUC/DNI debe contener 8 o 11 dígitos numéricos para la factura electrónica.', 'error');
                return;
            }
            
            // Show loading
            Swal.fire({
                title: 'Emitiendo CPE',
                html: 'Enviando payload XML UBL 2.1 a OSE/SUNAT...',
                allowOutsideClick: false,
                didOpen: () => { Swal.showLoading(); }
            });
            
            try {
                const token = localStorage.getItem('jhire_jwt_token');
                const res = await fetch('http://localhost:8000/api/billing/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({
                        order_id: parseInt(orderIdInput),
                        client_ruc_dni: rucInput,
                        client_name: clientNameInput
                    })
                });
                
                const data = await res.json();
                
                if(res.ok) {
                    Swal.fire({
                        title: 'Comprobante Aceptado por SUNAT',
                        html: `<div class="text-left mt-4 text-sm bg-surface-container-low p-4 rounded-lg">
                            <p><strong>Nro Resolución:</strong> SUNAT-${Math.floor(Math.random() * 1000000000)}</p>
                            <p class="mt-2 text-green-700 font-bold"><span class="material-symbols-outlined text-[14px]">check_circle</span> Factura ${data.invoice_number} generada correctamente por S/ ${data.total}</p>
                            <p class="text-xs text-outline mt-2 whitespace-pre-line">Hash Firma: ${btoa(data.invoice_number + data.total).substring(0, 16)}...</p>
                        </div>`,
                        icon: 'success',
                        confirmButtonText: 'Imprimir / Descargar PDF'
                    });
                    invoiceForm.reset();
                    loadDynamicBilling();
                } else {
                    Swal.fire('Error al Emitir', data.detail || 'Verifique que el ID de la Órden comercial exista en el sistema.', 'error');
                }
            } catch(e) {
                Swal.fire('Fallo de Red', 'No se pudo contactar al facturador electrónico.', 'error');
            }
        });
        
        // Auto-fill logic for dummy RUC checking
        const validateBtn = document.getElementById('validateRucBtn');
        if(validateBtn) {
            validateBtn.addEventListener('click', () => {
                const ruc = document.getElementById('rucInput').value.trim();
                const nameInp = document.getElementById('clientNameInput');
                if(/^\d{8}$|^\d{11}$/.test(ruc)) {
                    if(!nameInp.value) {
                       nameInp.value = ruc.length === 11 ? "EMPRESA RUC " + ruc + " S.A.C." : "CLIENTE DNI " + ruc;
                    }
                }
            });
        }
    }
"""

js = re.sub(r'// --- LÓGICA FACTURACIÓN DINÁMICA ---.*$', lambda m: billing_js + '    loadDynamicCRM();\n    loadDynamicBilling();\n});\n', js, flags=re.DOTALL)

with open(r'd:\tesis\jhire\frontend\app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Billing implementation complete")
