from pydantic import BaseModel, EmailStr
from typing import Optional

class Product(BaseModel):
    name: str
    price: float
    inventory: int
    size: str
    category: str
    image: Optional[str]
    cost: float

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

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserLoginResponse(BaseModel):
    access_token: str
    first_name: str
