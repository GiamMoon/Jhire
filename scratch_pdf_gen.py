import re
import os

# 1. Update backend billing.py to add /api/billing/{id}/pdf endpoint

billing_py_path = r'd:\tesis\jhire\backend\app\presentation\routers\billing.py'
with open(billing_py_path, 'r', encoding='utf-8') as f:
    billing_code = f.read()

pdf_endpoint_code = """
@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    import os
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
        
    filepath = f"factura_{invoice.invoice_number}.pdf"
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # -----------------------------
    # 1. EMISOR Y RECUADRO SUNAT
    # -----------------------------
    # Logo / Nombre Empresa Izquierda
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, height - 60, "JHIRE S.A.C.")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 75, "Av. Industrial 1234, Lima, Perú")
    c.drawString(40, height - 90, "Teléfono: (01) 555-1234")
    c.drawString(40, height - 105, "contacto@jhire.com.pe")
    
    # Recuadro Derecho SUNAT
    c.setLineWidth(1)
    c.rect(width - 250, height - 120, 200, 80)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width - 150, height - 60, "RUC: 20123456789")
    c.drawCentredString(width - 150, height - 80, "FACTURA ELECTRÓNICA")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width - 150, height - 100, f"{invoice.invoice_number}")
    
    # -----------------------------
    # 2. DATOS DEL CLIENTE
    # -----------------------------
    c.roundRect(40, height - 210, width - 80, 70, 5)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 160, "SEÑOR(ES):")
    c.drawString(50, height - 175, "RUC/DNI:")
    c.drawString(50, height - 190, "FECHA EMISIÓN:")
    
    c.setFont("Helvetica", 10)
    c.drawString(130, height - 160, f"{invoice.client_name}")
    c.drawString(130, height - 175, f"{invoice.client_ruc_dni}")
    c.drawString(130, height - 190, f"{invoice.issue_date.strftime('%Y-%m-%d')}")
    
    # Moneda
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - 200, height - 190, "MONEDA:")
    c.setFont("Helvetica", 10)
    c.drawString(width - 140, height - 190, "SOLES (PEN)")
    
    # -----------------------------
    # 3. DETALLE DE ÍTEMS
    # -----------------------------
    # Cabecera Tabla
    c.setFillColor(colors.lightgrey)
    c.rect(40, height - 250, width - 80, 20, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 245, "CANT")
    c.drawString(100, height - 245, "DESCRIPCIÓN")
    c.drawString(400, height - 245, "V. UNIT")
    c.drawString(480, height - 245, "IMPORTE")
    
    # Contenido (1 item genérico apuntando al Order)
    c.setFont("Helvetica", 10)
    y_item = height - 270
    c.drawString(55, y_item, "1.00")
    c.drawString(100, y_item, f"Consolidados de venta e ítems según Orden Comercial #{invoice.order_id}")
    c.drawString(400, y_item, f"S/ {invoice.subtotal:.2f}")
    c.drawString(480, y_item, f"S/ {invoice.subtotal:.2f}")
    
    # Líneas de la tabla
    c.rect(40, height - 500, width - 80, 250)
    
    # -----------------------------
    # 4. TOTALES
    # -----------------------------
    # Recuadro Totales (Abajo a la derecha)
    c.rect(width - 220, height - 580, 180, 60)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - 210, height - 540, "OP. GRAVADAS:")
    c.drawString(width - 210, height - 555, "IGV (18%):")
    c.drawString(width - 210, height - 570, "IMPORTE TOTAL:")
    
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 50, height - 540, f"S/ {invoice.subtotal:.2f}")
    c.drawRightString(width - 50, height - 555, f"S/ {invoice.igv:.2f}")
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 50, height - 570, f"S/ {invoice.total:.2f}")
    
    # Son:
    c.setFont("Helvetica", 9)
    c.drawString(40, height - 530, f"SON: AUTOMATIZADO CON EXPRESIÓN NUMÉRICA SOLES")
    
    # Footer Legal
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 50, "Representación Impresa de la FACTURA ELECTRÓNICA. Consúltela en la clave SOL.")
    c.drawCentredString(width / 2, 40, "Generado por JHIRE ERP 2026.")
    
    c.save()
    return FileResponse(filepath, filename=f"factura_{invoice.invoice_number}.pdf", media_type="application/pdf")
"""

if "def download_invoice_pdf(" not in billing_code:
    with open(billing_py_path, 'a', encoding='utf-8') as f:
        f.write("\n" + pdf_endpoint_code)
    print("Added PDF endpoint to billing.py")
else:
    print("PDF endpoint already in billing.py")

# 2. Update app.js to open PDF upon confirmation

app_js_path = r'd:\tesis\jhire\frontend\app.js'
with open(app_js_path, 'r', encoding='utf-8') as f:
    js_code = f.read()

# Replace Sweetalert inside invoiceForm.addEventListener('submit'
old_swal = """                    Swal.fire({
                        title: 'Comprobante Aceptado por SUNAT',
                        html: `<div class="text-left mt-4 text-sm bg-surface-container-low p-4 rounded-lg">
                            <p><strong>Nro Resolución:</strong> SUNAT-${Math.floor(Math.random() * 1000000000)}</p>
                            <p class="mt-2 text-green-700 font-bold"><span class="material-symbols-outlined text-[14px]">check_circle</span> Factura ${data.invoice_number} generada correctamente por S/ ${data.total}</p>
                            <p class="text-xs text-outline mt-2 whitespace-pre-line">Hash Firma: ${btoa(data.invoice_number + data.total).substring(0, 16)}...</p>
                        </div>`,
                        icon: 'success',
                        confirmButtonText: 'Imprimir / Descargar PDF'
                    });"""

new_swal = """                    Swal.fire({
                        title: 'Comprobante Aceptado por SUNAT',
                        html: `<div class="text-left mt-4 text-sm bg-surface-container-low p-4 rounded-lg" style="user-select: text;">
                            <p><strong>Nro Resolución:</strong> SUNAT-${Math.floor(Math.random() * 1000000000)}</p>
                            <p class="mt-2 text-green-700 font-bold"><span class="material-symbols-outlined text-[14px]">check_circle</span> Factura ${data.invoice_number} generada correctamente por S/ ${parseFloat(data.total).toFixed(2)}</p>
                            <p class="text-xs text-outline mt-2 whitespace-pre-line break-all">Hash Firma: ${btoa(data.invoice_number + data.total)}</p>
                        </div>`,
                        icon: 'success',
                        confirmButtonText: 'Imprimir / Descargar PDF',
                        showCancelButton: true,
                        cancelButtonText: 'Cerrar'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            window.open(`http://localhost:8000/api/billing/${data.id}/pdf`, '_blank');
                        }
                    });"""

if old_swal in js_code:
    js_code = js_code.replace(old_swal, new_swal)
    print("Replaced SweetAlert in app.js completion handler")
else:
    print("Could not find old_swal inside app.js")

# Modify "Últimos Emitidos" to have a download button in the SweetAlert info dialog!
old_info_click = """onclick="Swal.fire({title: 'Detalle de Comprobante', html: '<p><strong>Factura:</strong> ${i.invoice_number}</p><p><strong>Cliente:</strong> ${i.client_name}</p><p><strong>RUC:</strong> ${i.client_ruc_dni}</p><br><p><strong>Subtotal:</strong> S/ ${i.subtotal}</p><p><strong>IGV (18%):</strong> S/ ${i.igv}</p><p><strong>Total:</strong> S/ ${i.total}</p>', icon: 'info'})\""""

new_info_click = """onclick="Swal.fire({title: 'Detalle Comprobante Fiscal', html: '<div style=\\'text-align:left;font-size:14px;\\' class=\\'bg-surface-container-low p-4 rounded-lg\\'><p><strong>${i.invoice_number}</strong></p><p><strong>RUC:</strong> ${i.client_ruc_dni}</p><p><strong>Razón:</strong> ${i.client_name}</p><hr style=\\'margin:10px 0;border-color:#ccc\\'><div style=\\'display:flex;justify-content:space-between\\'><p>Subtotal:</p> <p>S/ ${parseFloat(i.subtotal).toFixed(2)}</p></div><div style=\\'display:flex;justify-content:space-between\\'><p>IGV(18%):</p> <p>S/ ${parseFloat(i.igv).toFixed(2)}</p></div><div style=\\'display:flex;justify-content:space-between;font-weight:bold;margin-top:5px;\\'><p>Total:</p> <p>S/ ${parseFloat(i.total).toFixed(2)}</p></div></div>', icon: 'info', showCancelButton: true, confirmButtonText: 'Ver representación (PDF)', cancelButtonText: 'Cerrar'}).then((res)=>{ if(res.isConfirmed){ window.open('http://localhost:8000/api/billing/'+i.id+'/pdf', '_blank'); } })\""""

if old_info_click in js_code:
    js_code = js_code.replace(old_info_click, new_info_click)
    print("Replaced onclick info dialog in app.js")
else:
    print("Could not find old_info_click in app.js")

with open(app_js_path, 'w', encoding='utf-8') as f:
    f.write(js_code)
