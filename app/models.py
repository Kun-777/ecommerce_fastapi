from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from .database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    size = Column(String, nullable=True)
    category = Column(String, nullable=False, server_default='other')
    inventory = Column(Integer, nullable=False, default=0)
    cost = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    image = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    is_admin = Column(Boolean, nullable=False, server_default="False")
    is_verified = Column(Boolean, nullable=False, server_default="False")

class CartItem(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    user = relationship("User")
    product = relationship("Product")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    quantity = Column(Integer, nullable=False)