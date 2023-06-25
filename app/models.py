from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False, unique=True)
    price = Column(Float, nullable=False)
    inventory = Column(Integer, nullable=False, default=0)
    size = Column(String, nullable=False)
    category = Column(String, nullable=False, server_default='other')
    image = Column(String, nullable=True)
    cost = Column(Float, nullable=False)

class User(Base):
    __tablename__ = "users"
    email = Column(String, nullable=False, primary_key=True)
    username = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    is_admin = Column(Boolean, nullable=False, server_default="False")
    is_verified = Column(Boolean, nullable=False, server_default="False")

