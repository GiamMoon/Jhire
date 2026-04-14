from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ...infrastructure.database import get_db
from ...infrastructure.models import ContactMessage
from ...domain.schemas import ContactMessageCreate, ContactMessageResponse

router = APIRouter()

def send_notification_email(contact_data: ContactMessageCreate):
    # Configuración de variables de entorno o credenciales
    sender_email = "giampierdelacruz37@gmail.com"
    sender_password = "icpiplormmznyolw"
    receiver_email = "elmer.escobillas@gmail.com"
    
    subject = f"Nuevo Contacto Comercial: {contact_data.name}"
    body = f"""
    Se ha recibido un nuevo formulario de contacto en JHIRE.
    
    Nombre: {contact_data.name}
    Empresa: {contact_data.company or 'N/A'}
    Teléfono: {contact_data.phone or 'N/A'}
    Email: {contact_data.email}
    
    Mensaje:
    {contact_data.message}
    """
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Se requiere conectar a un servidor SMTP (Ej: Gmail)
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            # Si las credenciales no son válidas, fallará silenciosamente
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("Correo de contacto enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

@router.post("/", response_model=ContactMessageResponse, status_code=status.HTTP_201_CREATED)
def create_contact_message(message: ContactMessageCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Guardar en Base de Datos
    db_message = ContactMessage(
        name=message.name,
        email=message.email,
        phone=message.phone,
        company=message.company,
        message=message.message
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # 2. Enviar correo en hilo secundario para no bloquear al usuario
    background_tasks.add_task(send_notification_email, message)
    
    return db_message
