from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class Product(BaseModel):
    name: str
    price: float
    inventory: int
    size: str
    category: str
    subcategory: Optional[str]
    description: Optional[str]
    popularity: int

class ProductResponse(Product):
    id: int
    class Config:
        orm_mode = True

class ProductAdminResponse(Product):
    id: int
    sku: int
    image: Optional[str]
    cost: float
    created_at: datetime
    class Config:
        orm_mode = True

class ProductAdminCreate(Product):
    sku: int
    cost: float
    image: Optional[str]

class ProductAdminUpdate(BaseModel):
    sku: Optional[int]
    name: Optional[str]
    price: Optional[float]
    inventory: Optional[int]
    size: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    description: Optional[str]
    cost: Optional[float]
    image: Optional[str]
    popularity: Optional[int]

class CategoryResponse(BaseModel):
    category: str
    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str

class UserProfileChange(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str

class UserProfileResponse(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    class Config:
        orm_mode = True

class Address(BaseModel):
    address_line_1: str
    address_line_2: Optional[str]
    city: str
    state: str
    zip_code: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserChangePassword(BaseModel):
    old_password: str
    new_password: str

class CartItem(Product):
    id: int # product id
    quantity: int
    synced: bool

class UserCart(BaseModel):
    items: List[CartItem]

class OrderItem(BaseModel):
    id: int
    product: ProductResponse
    quantity: int
    class Config:
        orm_mode = True

class OrderCreate(BaseModel):
    items: List[CartItem]
    order_type: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    schedule: Optional[str]
    tip: Optional[float]

class OrderResponse(BaseModel):
    id: int
    order_type: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    schedule: Optional[str]
    subtotal: float
    tip: Optional[float]
    total: float
    status: str
    reference_id: Optional[str]
    created_at: datetime
    cancel_reason: Optional[str]
    class Config:
        orm_mode = True

class OrderDetailResponse(OrderResponse):
    items: List[OrderItem]
    class Config:
        orm_mode = True

class OrderCancel(BaseModel):
    reason: str