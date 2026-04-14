from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

class UserBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    profile_picture_url: Optional[str] = None

class UserResponse(UserBase):
    id: int
    email: str
    role: str
    profile_picture_url: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price_soles: float
    image_url: Optional[str] = None
    stock: int

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

from typing import List
from datetime import datetime

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    product: ProductResponse
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_price: float
    created_at: datetime
    items: List[OrderItemResponse]
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: str

class ContactMessageCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    message: str

class ContactMessageResponse(ContactMessageCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class InvoiceCreate(BaseModel):
    order_id: int
    client_ruc_dni: str
    client_name: str

    @field_validator('client_ruc_dni')
    @classmethod
    def ruc_modulo11(cls, v: str) -> str:
        if len(v) == 8 and v.isdigit(): return v # Allow DNI
        if len(v) != 11 or not v.isdigit():
            raise ValueError("El RUC debe tener 11 dígitos numéricos")
        if not v.startswith(('10', '15', '16', '17', '20')):
            raise ValueError("RUC debe iniciar con 10, 15, 16, 17 o 20")
        
        multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        total = sum(int(v[i]) * multipliers[i] for i in range(10))
        rem = total % 11
        check = 11 - rem
        if check == 10: check = 0
        elif check == 11: check = 1
        
        if int(v[10]) != check:
            raise ValueError("RUC inválido según validación Módulo-11 de SUNAT")
        return v

class InvoiceResponse(BaseModel):
    id: int
    order_id: int
    invoice_number: str
    client_ruc_dni: str
    client_name: str
    subtotal: float
    igv: float
    total: float
    issue_date: datetime
    sunat_status: str
    
    class Config:
        from_attributes = True

class InventoryMovementCreate(BaseModel):
    product_id: int
    type: str # 'Entrada' or 'Salida'
    quantity: int
    description: Optional[str] = None

class SupplierResponse(BaseModel):
    id: int
    name: str
    lead_time_days: int
    
    class Config:
        from_attributes = True

class InventoryMovementResponse(InventoryMovementCreate):
    id: int
    date: datetime
    
    class Config:
        from_attributes = True

class ClientProfileCreate(BaseModel):
    ruc_dni: Optional[str] = None
    company_name: Optional[str] = None
    preferences: Optional[str] = None
    data_protection_consent: bool

    @field_validator('ruc_dni')
    @classmethod
    def ruc_modulo11(cls, v: Optional[str]) -> Optional[str]:
        if not v: return v
        if len(v) == 8 and v.isdigit(): return v # Allow DNI
        if len(v) != 11 or not v.isdigit():
            raise ValueError("El RUC debe tener 11 dígitos numéricos")
        if not v.startswith(('10', '15', '16', '17', '20')):
            raise ValueError("RUC debe iniciar con 10 o 20")
        
        multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        total = sum(int(v[i]) * multipliers[i] for i in range(10))
        rem = total % 11
        check = 11 - rem
        if check == 10: check = 0
        elif check == 11: check = 1
        
        if int(v[10]) != check:
            raise ValueError("RUC inválido según algoritmo Módulo-11")
        return v

class ClientProfileResponse(ClientProfileCreate):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

class PaymentInstallmentCreate(BaseModel):
    amount: float
    due_date: datetime

class PaymentInstallmentResponse(BaseModel):
    id: int
    invoice_id: int
    amount: float
    status: str
    due_date: datetime
    paid_date: Optional[datetime] = None

    class Config:
        from_attributes = True
