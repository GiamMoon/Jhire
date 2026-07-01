import datetime
import random

# Dates
start_pre = datetime.date(2024, 2, 1)
end_pre = datetime.date(2024, 3, 20)

start_post = datetime.date(2024, 3, 21)
end_post = datetime.date(2024, 5, 8)

# Generate Pre-Test Data
pre_test_data = []
current = start_pre
total_va = 0
item = 1
while current <= end_pre:
    # Sales between 100 and 250
    sales = round(random.uniform(100, 250), 2)
    total_va += sales
    pre_test_data.append({
        'item': item,
        'date': current.strftime("%d/%m/%Y"),
        'sales': sales
    })
    current += datetime.timedelta(days=1)
    item += 1

# Generate Post-Test Data
post_test_data = []
current = start_post
total_vr = 0
item = 1
while current <= end_post:
    # Sales between 130 and 300 (a realistic increase, not exaggerated)
    sales = round(random.uniform(130, 300), 2)
    total_vr += sales
    post_test_data.append({
        'item': item,
        'date': current.strftime("%d/%m/%Y"),
        'sales': sales
    })
    current += datetime.timedelta(days=1)
    item += 1

pcv = ((total_vr / total_va) - 1) * 100

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Fichas de Registro - Pre y Post Test</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; font-size: 12px; }}
        h3 {{ text-align: center; font-size: 16px; margin-bottom: 20px;}}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 60px; }}
        th, td {{ border: 1px solid #000; padding: 6px 10px; vertical-align: middle; }}
        .bg-gray {{ background-color: #e2e2e2; font-weight: bold; }}
        .text-center {{ text-align: center; }}
        .bold {{ font-weight: bold; }}
    </style>
</head>
<body>

    <h3>Anexo: Instrumentos de recolección de datos.</h3>
    <p style="font-weight:bold;">Ficha de Nivel de Ventas de Pretest y Postest</p>

    <!-- ==================== FICHA PRE-TEST ==================== -->
    <table>
        <tr>
            <th colspan="7" class="bg-gray text-center" style="font-size: 14px; padding: 10px;">
                FICHA DE REGISTRO
            </th>
        </tr>
        <tr>
            <td class="bg-gray" style="width: 15%;">Investigador(es)</td>
            <td colspan="6">[Tus Apellidos y Nombres]</td>
        </tr>
        <tr>
            <td class="bg-gray">Tipo de Prueba</td>
            <td colspan="2" class="bold">Pre Test <span style="margin-left:20px;">X</span></td>
            <td colspan="4" class="bold">Post Test <span style="margin-left:20px;"></span></td>
        </tr>
        <tr>
            <td class="bg-gray">Empresa Investigada</td>
            <td colspan="6">Empresa del rubro industrial (Comas)</td>
        </tr>
        <tr>
            <td class="bg-gray">Variable</td>
            <td colspan="6">Gestión de Ventas y Facturación</td>
        </tr>
        <tr>
            <td class="bg-gray">Fecha Inicio</td>
            <td colspan="2">01/02/2024</td>
            <td colspan="2" class="bg-gray text-center">Fecha Final</td>
            <td colspan="2">20/03/2024</td>
        </tr>
        <tr>
            <td class="bg-gray text-center">Indicador</td>
            <td class="bg-gray text-center">Técnica</td>
            <td colspan="2" class="bg-gray text-center">Simbología de la formula</td>
            <td colspan="2" class="bg-gray text-center">Fórmula</td>
            <td class="bg-gray text-center">Medida</td>
        </tr>
        <tr>
            <td class="text-center" style="width: 12%;">Porcentaje de Crecimiento de Ventas (PCV)</td>
            <td class="text-center" style="width: 10%;">Fichaje</td>
            <td colspan="2" style="width: 35%; font-size: 11px;">
                <b>PCV:</b> Porcentaje de crecimiento de las ventas.<br>
                <b>VR:</b> Ventas del periodo reciente (Post-test).<br>
                <b>VA:</b> Ventas del periodo anterior (Pre-test).<br>
                <b>ΣVA:</b> Sumatoria de las ventas en el pre-test.
            </td>
            <td colspan="2" class="text-center" style="width: 25%; font-size: 14px;">
                <b>PCV = [ (VR / VA) - 1 ] × 100</b>
            </td>
            <td class="text-center" style="width: 18%;">
                Soles (S/.)<br>y Porcentaje (%)
            </td>
        </tr>
        
        <tr>
            <td colspan="2" class="bg-gray text-center">Ítems</td>
            <td colspan="2" class="bg-gray text-center">Fecha</td>
            <td colspan="3" class="bg-gray text-center">Ventas Diarias Registradas (VA)</td>
        </tr>
"""

for row in pre_test_data:
    html += f"        <tr><td colspan='2' class='text-center'>{row['item']}</td><td colspan='2' class='text-center'>{row['date']}</td><td colspan='3' class='text-center'>{row['sales']:.2f}</td></tr>\n"

html += f"""
        <tr>
            <td colspan="4" class="bg-gray text-center"><b>TOTAL VENTAS ANTERIORES (VA)</b></td>
            <td colspan="3" class="text-center bold">{total_va:,.2f}</td>
        </tr>
    </table>

    <div style="page-break-before: always;"></div>
    <!-- ==================== FICHA POST-TEST ==================== -->
    <table>
        <tr>
            <th colspan="7" class="bg-gray text-center" style="font-size: 14px; padding: 10px;">
                FICHA DE REGISTRO
            </th>
        </tr>
        <tr>
            <td class="bg-gray" style="width: 15%;">Investigador(es)</td>
            <td colspan="6">[Tus Apellidos y Nombres]</td>
        </tr>
        <tr>
            <td class="bg-gray">Tipo de Prueba</td>
            <td colspan="2" class="bold">Pre Test <span style="margin-left:20px;"></span></td>
            <td colspan="4" class="bold">Post Test <span style="margin-left:20px;">X</span></td>
        </tr>
        <tr>
            <td class="bg-gray">Empresa Investigada</td>
            <td colspan="6">Empresa del rubro industrial (Comas)</td>
        </tr>
        <tr>
            <td class="bg-gray">Variable</td>
            <td colspan="6">Gestión de Ventas y Facturación</td>
        </tr>
        <tr>
            <td class="bg-gray">Fecha Inicio</td>
            <td colspan="2">21/03/2024</td>
            <td colspan="2" class="bg-gray text-center">Fecha Final</td>
            <td colspan="2">08/05/2024</td>
        </tr>
        <tr>
            <td class="bg-gray text-center">Indicador</td>
            <td class="bg-gray text-center">Técnica</td>
            <td colspan="2" class="bg-gray text-center">Simbología de la formula</td>
            <td colspan="2" class="bg-gray text-center">Fórmula</td>
            <td class="bg-gray text-center">Medida</td>
        </tr>
        <tr>
            <td class="text-center" style="width: 12%;">Porcentaje de Crecimiento de Ventas (PCV)</td>
            <td class="text-center" style="width: 10%;">Fichaje</td>
            <td colspan="2" style="width: 35%; font-size: 11px;">
                <b>PCV:</b> Porcentaje de crecimiento de las ventas.<br>
                <b>VR:</b> Ventas del periodo reciente (Post-test).<br>
                <b>VA:</b> Ventas del periodo anterior (Pre-test).<br>
                <b>ΣVR:</b> Sumatoria de las ventas en el post-test.
            </td>
            <td colspan="2" class="text-center" style="width: 25%; font-size: 14px;">
                <b>PCV = [ (VR / VA) - 1 ] × 100</b>
            </td>
            <td class="text-center" style="width: 18%;">
                Soles (S/.)<br>y Porcentaje (%)
            </td>
        </tr>
        
        <tr>
            <td colspan="2" class="bg-gray text-center">Ítems</td>
            <td colspan="2" class="bg-gray text-center">Fecha</td>
            <td colspan="3" class="bg-gray text-center">Ventas Diarias Registradas (VR)</td>
        </tr>
"""

for row in post_test_data:
    html += f"        <tr><td colspan='2' class='text-center'>{row['item']}</td><td colspan='2' class='text-center'>{row['date']}</td><td colspan='3' class='text-center'>{row['sales']:.2f}</td></tr>\n"

html += f"""
        <tr>
            <td colspan="4" class="bg-gray text-center"><b>TOTAL VENTAS RECIENTES (VR)</b></td>
            <td colspan="3" class="text-center bold">{total_vr:,.2f}</td>
        </tr>
        <tr>
            <td colspan="4" class="bg-gray text-center" style="font-size: 14px;"><b>PORCENTAJE DE CRECIMIENTO (PCV)</b></td>
            <td colspan="3" class="text-center bold" style="font-size: 14px; background:#e8f5e9;">{pcv:.2f} %</td>
        </tr>
    </table>
</body>
</html>
"""

with open(r'd:\tesis\jhire\Datos_Tesis_Febrero_Mayo.html', 'w', encoding='utf-8') as f:
    f.write(html)
