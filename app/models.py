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
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    password = Column(String, nullable=False)
    # optional address fields
    address_line_1 = Column(String, nullable=True)
    address_line_2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)

    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))
    is_admin = Column(Boolean, nullable=False, server_default="False")
    is_verified = Column(Boolean, nullable=False, server_default="False")
    orders = relationship("Order", backref="user")

class CartItem(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    user = relationship("User")
    product = relationship("Product")
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))
    quantity = Column(Integer, nullable=False)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    subtotal = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    order_type = Column(String, nullable=False) # delivery or pick up
    status = Column(String, nullable=False) # created, placed, confirmed, completed
    # customer Info fields
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    # optional address fields
    address_line_1 = Column(String, nullable=True)
    address_line_2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    # non empty if order is scheduled
    schedule = Column(String, nullable=True)
    tip = Column(Float, nullable=True)
    
    cancel_reason = Column(String, nullable=True)

    reference_id = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))
    items = relationship('OrderItem', backref='order')

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    product = relationship("Product")
    quantity = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))