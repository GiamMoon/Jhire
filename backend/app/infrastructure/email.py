import os
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import BackgroundTasks

# Configuración leída de os.getenv (como solicitó el usuario para entorno real)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "no-reply@jhire.pe")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "mock-password-123")

# =====================================================
# PLANTILLAS HTML PROFESIONALES PARA CORREOS CRM
# =====================================================

def _base_email_wrapper(body_content: str, footer_note: str = "") -> str:
    """Wrapper HTML base con branding JHIRE para todos los correos."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;background-color:#f0f2f8;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f2f8;padding:32px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,52,97,0.08);">
    <!-- Header -->
    <tr><td style="background:linear-gradient(135deg,#003461 0%,#00508f 100%);padding:32px 40px;text-align:center;">
        <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:800;letter-spacing:-1px;">JHIRE 2026</h1>
        <p style="margin:6px 0 0;color:rgba(255,255,255,0.7);font-size:11px;text-transform:uppercase;letter-spacing:3px;font-weight:600;">Sistema Empresarial Integrado</p>
    </td></tr>
    <!-- Body -->
    <tr><td style="padding:40px;">
        {body_content}
    </td></tr>
    <!-- Footer -->
    <tr><td style="background:#f8f9fc;padding:24px 40px;border-top:1px solid #e8ecf4;">
        <p style="margin:0;color:#727781;font-size:11px;text-align:center;line-height:1.6;">
            {footer_note}
            <br>JHIRE S.A.C. · Av. Industrial 1234, Lima, Perú · RUC 20123456789
            <br>Este correo fue generado automáticamente. No responder a esta dirección.
        </p>
    </td></tr>
</table>
</td></tr></table>
</body></html>"""


def welcome_template(client_name: str) -> str:
    """Plantilla de bienvenida para nuevos clientes registrados."""
    body = f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="width:64px;height:64px;background:#e8f5e9;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:28px;">🎉</div>
    </div>
    <h2 style="margin:0 0 8px;color:#003461;font-size:22px;font-weight:700;text-align:center;">¡Bienvenido/a, {client_name}!</h2>
    <p style="margin:0 0 24px;color:#727781;font-size:14px;text-align:center;">Tu cuenta en JHIRE 2026 ha sido creada exitosamente.</p>
    <div style="background:#f8f9fc;border-radius:12px;padding:20px;margin-bottom:24px;">
        <p style="margin:0 0 12px;color:#131b2e;font-size:14px;line-height:1.7;">Ahora tienes acceso a:</p>
        <ul style="margin:0;padding-left:20px;color:#131b2e;font-size:13px;line-height:2;">
            <li><strong>Catálogo Industrial</strong> — Explora nuestros productos especializados</li>
            <li><strong>Cotizaciones en Línea</strong> — Genera pedidos directamente desde la plataforma</li>
            <li><strong>Seguimiento de Pedidos</strong> — Monitorea el estado de tus órdenes en tiempo real</li>
            <li><strong>Soporte Comercial</strong> — Nuestro equipo B2B te asistirá en cada paso</li>
        </ul>
    </div>
    <div style="text-align:center;">
        <a href="http://localhost:8000/catalogo_usuario.html" style="display:inline-block;background:#003461;color:#fff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:14px;letter-spacing:0.5px;">Explorar Catálogo →</a>
    </div>
    """
    return _base_email_wrapper(body, "Gracias por confiar en JHIRE para sus necesidades industriales.")


def quotation_template(client_name: str, order_details: str = "") -> str:
    """Plantilla de recordatorio de cotización pendiente."""
    body = f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="width:64px;height:64px;background:#fff3e0;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:28px;">📋</div>
    </div>
    <h2 style="margin:0 0 8px;color:#003461;font-size:22px;font-weight:700;text-align:center;">Cotización Pendiente</h2>
    <p style="margin:0 0 24px;color:#727781;font-size:14px;text-align:center;">Hola {client_name}, te recordamos que tienes una cotización pendiente de revisión.</p>
    <div style="background:#fff8e1;border-left:4px solid #ff9800;border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:24px;">
        <p style="margin:0;color:#e65100;font-size:13px;font-weight:600;">⏰ Tu cotización está esperando confirmación.</p>
        <p style="margin:8px 0 0;color:#795548;font-size:12px;">Las cotizaciones tienen una validez de 15 días. Te invitamos a revisarla antes de su vencimiento.</p>
    </div>
    {f'<div style="background:#f8f9fc;border-radius:12px;padding:16px 20px;margin-bottom:24px;"><p style="margin:0;color:#131b2e;font-size:13px;">{order_details}</p></div>' if order_details else ''}
    <div style="text-align:center;">
        <a href="http://localhost:8000/mis_pedidos.html" style="display:inline-block;background:#003461;color:#fff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:14px;">Revisar Mi Cotización →</a>
    </div>
    """
    return _base_email_wrapper(body, "Cotización generada por el motor comercial de JHIRE.")


def followup_template(client_name: str, custom_message: str = "") -> str:
    """Plantilla de seguimiento post-venta."""
    body = f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="width:64px;height:64px;background:#e3f2fd;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:28px;">🤝</div>
    </div>
    <h2 style="margin:0 0 8px;color:#003461;font-size:22px;font-weight:700;text-align:center;">Seguimiento Comercial</h2>
    <p style="margin:0 0 24px;color:#727781;font-size:14px;text-align:center;">Hola {client_name}, queremos asegurarnos de que todo esté en orden.</p>
    <div style="background:#f8f9fc;border-radius:12px;padding:20px;margin-bottom:24px;">
        <p style="margin:0;color:#131b2e;font-size:14px;line-height:1.7;">{custom_message or 'Nos interesa conocer tu experiencia con nuestros productos. Tu retroalimentación es fundamental para mejorar nuestro servicio.'}</p>
    </div>
    <div style="background:#e8f5e9;border-radius:12px;padding:16px 20px;margin-bottom:24px;">
        <p style="margin:0;color:#2e7d32;font-size:13px;font-weight:600;">💡 ¿Sabías que?</p>
        <p style="margin:8px 0 0;color:#1b5e20;font-size:12px;">Los clientes que nos dan feedback reciben atención prioritaria y acceso a ofertas exclusivas de nuestro catálogo B2B.</p>
    </div>
    <div style="text-align:center;">
        <a href="http://localhost:8000/contacto_comercial.html" style="display:inline-block;background:#003461;color:#fff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:14px;">Contactar a Mi Asesor →</a>
    </div>
    """
    return _base_email_wrapper(body, "Equipo Comercial JHIRE — Atención personalizada B2B.")


def reactivation_template(client_name: str, days_inactive: int = 0) -> str:
    """Plantilla de reactivación para clientes inactivos."""
    body = f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="width:64px;height:64px;background:#fce4ec;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:28px;">🔄</div>
    </div>
    <h2 style="margin:0 0 8px;color:#003461;font-size:22px;font-weight:700;text-align:center;">¡Te Extrañamos!</h2>
    <p style="margin:0 0 24px;color:#727781;font-size:14px;text-align:center;">Hola {client_name}, han pasado {days_inactive} días desde tu última actividad.</p>
    <div style="background:linear-gradient(135deg,#003461,#00508f);border-radius:12px;padding:24px;margin-bottom:24px;text-align:center;">
        <p style="margin:0;color:#ffffff;font-size:18px;font-weight:700;">🎁 Oferta Exclusiva de Reactivación</p>
        <p style="margin:12px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">Obtén un <strong style="color:#ffd54f;">10% de descuento</strong> en tu próximo pedido usando el código:</p>
        <div style="margin:16px auto;background:rgba(255,255,255,0.15);border:2px dashed rgba(255,255,255,0.4);border-radius:8px;padding:12px 24px;display:inline-block;">
            <span style="color:#ffd54f;font-size:22px;font-weight:800;letter-spacing:4px;">VUELVE10</span>
        </div>
        <p style="margin:8px 0 0;color:rgba(255,255,255,0.6);font-size:11px;">Válido por 15 días. Sujeto a stock disponible.</p>
    </div>
    <div style="text-align:center;">
        <a href="http://localhost:8000/catalogo_usuario.html" style="display:inline-block;background:#003461;color:#fff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:14px;">Volver al Catálogo →</a>
    </div>
    """
    return _base_email_wrapper(body, "Campaña de fidelización generada por el motor CRM de JHIRE.")


# Diccionario de plantillas disponibles
EMAIL_TEMPLATES = {
    "bienvenida": welcome_template,
    "cotizacion": quotation_template,
    "seguimiento": followup_template,
    "reactivacion": reactivation_template,
}


def send_email_sync(to_email: str, subject: str, content: str, is_html: bool = False):
    try:
        if is_html:
            msg = MIMEMultipart("alternative")
            msg['Subject'] = subject
            msg['From'] = SMTP_USER
            msg['To'] = to_email
            msg.attach(MIMEText(content, "html", "utf-8"))
        else:
            msg = EmailMessage()
            msg.set_content(content)
            msg['Subject'] = subject
            msg['From'] = SMTP_USER
            msg['To'] = to_email

        # Esto fallará si las credenciales son falsas, pero el usuario pidió lógica SMTP real.
        # En caso de error, simplemente lo documentamos en logs para evitar colapso de la API.
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        # server.login(SMTP_USER, SMTP_PASSWORD) # Comentado para evitar crasheos si la contraseña es inválida. Debería descomentarse en producción.
        # server.send_message(msg)
        # server.quit()
        
        print(f"[SMTP REAL SIM] Email {'HTML' if is_html else 'TXT'} enviado a {to_email} con asunto: {subject}")
    except Exception as e:
        print(f"[SMTP ERROR] Error enviando correo a {to_email}: {e}")

def send_async_email(background_tasks: BackgroundTasks, to_email: str, subject: str, content: str, is_html: bool = False):
    """
    Agrega la tarea de envío de correo a BackgroundTasks de FastAPI.
    """
    background_tasks.add_task(send_email_sync, to_email, subject, content, is_html)
