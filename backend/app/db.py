import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./food.db')

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    sort_order = Column(Integer, default=0)
    products = relationship('Product', back_populates='category')

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'))
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    image = Column(String)
    tags = Column(String)
    rating = Column(Float, default=0.0)
    category = relationship('Category', back_populates='products')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    name = Column(String)
    phone = Column(String)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    items_json = Column(Text)
    total_price = Column(Float)
    address = Column(String)
    phone = Column(String)
    payment_method = Column(String)
    status = Column(String, default='new')
    created_at = Column(DateTime, default=datetime.utcnow)


class Cart(Base):
    __tablename__ = 'carts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    # items stored as JSON for simplicity
    items_json = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)


class CartItem(Base):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('carts.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    qty = Column(Integer, default=1)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_sample_data():
    from sqlalchemy import select
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Category))
        if res.scalars().first():
            return
        c1 = Category(title='Роллы')
        c2 = Category(title='Сэндвич-роллы')
        c3 = Category(title='Супы')
        s.add_all([c1, c2, c3])
        await s.flush()
        p1 = Product(name='Классический ролл', description='Рис, нори, лосось', price=450.0, category=c1, image='', tags='Новинка', rating=4.5)
        p2 = Product(name='Фирменный ролл', description='Тёплый ролл с сыром', price=520.0, category=c1, image='', tags='Выбор шефа', rating=4.8)
        p3 = Product(name='Чикен ролл', description='Курочка и соус', price=350.0, category=c2, image='', tags='', rating=4.2)
        p4 = Product(name='Морковный суп', description='Тёплый овощной суп', price=230.0, category=c3, image='', tags='Новинка', rating=4.0)
        p5 = Product(name='Мiso суп', description='Японский суп', price=260.0, category=c3, image='', tags='Выбор месяца', rating=4.6)
        s.add_all([p1, p2, p3, p4, p5])
        await s.commit()
