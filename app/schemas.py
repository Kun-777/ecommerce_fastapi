from pydantic import BaseModel, EmailStr
from typing import Optional, List

class Product(BaseModel):
    name: str
    price: float
    inventory: int
    size: str
    category: str
    image: Optional[str]

class ProductResponse(Product):
    id: int
    class Config:
        orm_mode = True

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

class UserProfile(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserLoginResponse(BaseModel):
    access_token: str
    first_name: str

class UserChangePassword(BaseModel):
    old_password: str
    new_password: str

class CartItem(Product):
    id: int # product id
    quantity: int
    synced: bool

class UserCart(BaseModel):
    cart: List[CartItem]