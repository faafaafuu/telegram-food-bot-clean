from typing import List
import json
import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

import config

DATABASE_URL = config.DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    image_url = Column(String)
    tags = Column(String)  # comma-separated
    rating = Column(Float, default=0.0)
    category = relationship("Category", back_populates="products")

class Cart(Base):
    __tablename__ = 'cart'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'))
    qty = Column(Integer, default=1)
    product = relationship("Product")

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    items_json = Column(Text)
    total_price = Column(Float)
    address = Column(String)
    phone = Column(String)
    payment_method = Column(String)
    status = Column(String, default='new')
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String)
    phone = Column(String)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# Simple CRUD helpers
async def get_categories(session: AsyncSession) -> List[Category]:
    result = await session.execute("SELECT * FROM categories")
    # For simplicity in this minimal example we use ORM queries:
    return await session.scalars(Category.__table__.select())

async def create_sample_data():
    async with AsyncSessionLocal() as s:
        # check categories
        q = await s.execute(Category.__table__.select())
        rows = q.all()
        if rows:
            return
        c1 = Category(title='Роллы')
        c2 = Category(title='Сэндвич-роллы')
        c3 = Category(title='Супы')
        s.add_all([c1, c2, c3])
        await s.flush()
        p1 = Product(name='Классический ролл', description='Рис, нори, лосось', price=450.0, category=c1, image_url='https://images.unsplash.com/photo-1562967916-eb82221dfb36', tags='Новинка', rating=4.5)
        p2 = Product(name='Фирменный ролл', description='Тёплый ролл с сыром', price=520.0, category=c1, image_url='https://images.unsplash.com/photo-1546069901-ba9599a7e63c', tags='Выбор шефа', rating=4.8)
        p3 = Product(name='Чикен ролл', description='Курочка и соус', price=350.0, category=c2, image_url='https://images.unsplash.com/photo-1604908177522-7d44e1a1b3e1', tags='', rating=4.2)
        p4 = Product(name='Морковный суп', description='Тёплый овощной суп', price=230.0, category=c3, image_url='https://images.unsplash.com/photo-1504674900247-0877df9cc836', tags='Новинка', rating=4.0)
        p5 = Product(name='Мiso суп', description='Японский суп', price=260.0, category=c3, image_url='https://images.unsplash.com/photo-1517248135467-4c7edcad34c4', tags='Выбор месяца', rating=4.6)
        s.add_all([p1, p2, p3, p4, p5])
        await s.commit()


# Small helper functions used by handlers
async def list_categories(session: AsyncSession):
    result = await session.execute(Category.__table__.select())
    rows = result.all()
    return rows

async def get_products_by_category(session: AsyncSession, category_id: int):
    q = Product.__table__.select().where(Product.category_id == category_id)
    res = await session.execute(q)
    return res.all()

async def get_product(session: AsyncSession, product_id: int):
    res = await session.execute(Product.__table__.select().where(Product.id == product_id))
    row = res.first()
    return row

async def add_to_cart(session: AsyncSession, user_id: int, product_id: int, qty: int = 1):
    item = Cart(user_id=user_id, product_id=product_id, qty=qty)
    session.add(item)
    await session.commit()
    return item

async def get_cart_items(session: AsyncSession, user_id: int):
    q = Cart.__table__.select().where(Cart.user_id == user_id)
    res = await session.execute(q)
    return res.all()
