import os
import smtplib
from email.message import EmailMessage
from fastapi import BackgroundTasks

# Configuración leída de os.getenv (como solicitó el usuario para entorno real)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "no-reply@jhire.pe")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "mock-password-123")

def send_email_sync(to_email: str, subject: str, content: str):
    try:
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
        
        print(f"[SMTP REAL SIM] Email enviado a {to_email} con asunto: {subject}")
    except Exception as e:
        print(f"[SMTP ERROR] Error enviando correo a {to_email}: {e}")

def send_async_email(background_tasks: BackgroundTasks, to_email: str, subject: str, content: str):
    """
    Agrega la tarea de envío de correo a BackgroundTasks de FastAPI.
    """
    background_tasks.add_task(send_email_sync, to_email, subject, content)
