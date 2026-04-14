from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.infrastructure.models import Product
from app.domain.schemas import ChatRequest, ChatResponse
from app.domain.services.llm_service import llm_service

router = APIRouter(
    tags=["Chatbot"]
)

@router.post("/", response_model=ChatResponse)
def handle_chat_message(request: ChatRequest, db: Session = Depends(get_db)):
    # 1. Fetch catalog context from DB
    products = db.query(Product).all()
    
    # 2. Build string context
    context_lines = []
    for p in products:
        desc = p.description if p.description else "No description"
        context_lines.append(f"- ID: {p.id} | Nombre: {p.name} | Precio: S/{p.price_soles} | Stock: {p.stock} | Link de compra: detalle_producto.html?id={p.id} | Resumen: {desc}")
    
    context_str = "\n".join(context_lines)
    if not context_str:
        context_str = "No products currently available."
        
    # 3. Generate response using local AI service
    response_text = llm_service.generate_response(context_str, request.message)
    
    return ChatResponse(response=response_text)
