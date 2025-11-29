from pydantic import BaseModel
from typing import List, Optional

class CategoryOut(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    image: Optional[str]
    tags: Optional[str]
    rating: Optional[float]
    category_id: Optional[int]

    class Config:
        orm_mode = True

class AddCartItem(BaseModel):
    product_id: int
    qty: int = 1


class CategoryIn(BaseModel):
    title: str
    sort_order: int = 0


class ProductIn(BaseModel):
    name: str
    category_id: int
    description: Optional[str] = None
    price: float
    image: Optional[str] = None
    tags: Optional[str] = None
    rating: Optional[float] = None


class CategoryOut(BaseModel):
    id: int
    title: str
    sort_order: int
    class Config:
        orm_mode = True


class ProductOut(BaseModel):
    id: int
    name: str
    category_id: int
    description: Optional[str]
    price: float
    image: Optional[str]
    tags: Optional[str]
    rating: Optional[float]
    class Config:
        orm_mode = True

class CreateOrder(BaseModel):
    tg_id: int
    items: List[dict]
    total_price: float
    address: Optional[str]
    phone: Optional[str]
    payment_method: str
    name: Optional[str]
