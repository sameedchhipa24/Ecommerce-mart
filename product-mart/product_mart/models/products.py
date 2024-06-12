from datetime import datetime
from typing import List, Optional
import uuid
from sqlmodel import Field, SQLModel

class ProductBase(SQLModel):
    name: str
    description: str
    price: float
    slug: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    images: str  # Storing image file paths as a comma-separated string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})

