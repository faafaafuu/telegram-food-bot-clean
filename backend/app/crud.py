from .db import AsyncSessionLocal, Category, Product, User, Order
from sqlalchemy import select
import json
from datetime import datetime
from .db import Cart
from sqlalchemy import delete, update

async def list_categories():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Category))
        return [c for c in res.scalars().all()]


async def create_category(data: dict):
    async with AsyncSessionLocal() as s:
        c = Category(title=data.get('title'), sort_order=data.get('sort_order', 0))
        s.add(c)
        await s.commit()
        await s.refresh(c)
        return c


async def update_category(cat_id: int, data: dict):
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Category).where(Category.id == cat_id))
        c = res.scalars().first()
        if not c:
            return None
        c.title = data.get('title', c.title)
        c.sort_order = data.get('sort_order', c.sort_order)
        await s.commit()
        return c


async def delete_category(cat_id: int):
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Category).where(Category.id == cat_id))
        c = res.scalars().first()
        if not c:
            return False
        await s.delete(c)
        await s.commit()
        return True

async def list_products(category_id: int = None):
    async with AsyncSessionLocal() as s:
        if category_id:
            res = await s.execute(select(Product).where(Product.category_id == category_id))
        else:
            res = await s.execute(select(Product))
        return [p for p in res.scalars().all()]


async def create_product(data: dict):
    async with AsyncSessionLocal() as s:
        p = Product(name=data.get('name'), category_id=data.get('category_id'), description=data.get('description'), price=data.get('price'), image=data.get('image'), tags=data.get('tags'), rating=data.get('rating'))
        s.add(p)
        await s.commit()
        await s.refresh(p)
        return p


async def update_product(product_id: int, data: dict):
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Product).where(Product.id == product_id))
        p = res.scalars().first()
        if not p:
            return None
        p.name = data.get('name', p.name)
        p.category_id = data.get('category_id', p.category_id)
        p.description = data.get('description', p.description)
        p.price = data.get('price', p.price)
        p.image = data.get('image', p.image)
        p.tags = data.get('tags', p.tags)
        p.rating = data.get('rating', p.rating)
        await s.commit()
        return p


async def delete_product(product_id: int):
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Product).where(Product.id == product_id))
        p = res.scalars().first()
        if not p:
            return False
        await s.delete(p)
        await s.commit()
        return True


async def export_products_csv():
    import csv, io
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Product))
        products = res.scalars().all()
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(['id','name','category_id','description','price','tags','rating'])
        for p in products:
            writer.writerow([p.id, p.name, p.category_id, p.description or '', p.price or 0, p.tags or '', p.rating or 0])
        return buf.getvalue()

async def add_to_cart(user_id: int, product_id: int, qty: int = 1):
    async with AsyncSessionLocal() as s:
        # find user
        res = await s.execute(select(User).where(User.tg_id == user_id))
        user = res.scalars().first()
        if not user:
            user = User(tg_id=user_id)
            s.add(user)
            await s.flush()
        # find cart
        res2 = await s.execute(select(Cart).where(Cart.user_id == user.id))
        cart = res2.scalars().first()
        if not cart:
            cart = Cart(user_id=user.id, items_json=json.dumps([]), updated_at=datetime.utcnow())
            s.add(cart)
            await s.flush()
        items = json.loads(cart.items_json or '[]')
        found = False
        for it in items:
            if it.get('product_id') == product_id:
                it['qty'] = it.get('qty', 0) + qty
                found = True
                break
        if not found:
            items.append({'product_id': product_id, 'qty': qty})
        cart.items_json = json.dumps(items)
        cart.updated_at = datetime.utcnow()
        await s.commit()
        return {"ok": True, "items": items}

async def get_cart(user_id: int):
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(User).where(User.tg_id == user_id))
        user = res.scalars().first()
        if not user:
            return {"items": []}
        res2 = await s.execute(select(Cart).where(Cart.user_id == user.id))
        cart = res2.scalars().first()
        if not cart:
            return {"items": []}
        items = json.loads(cart.items_json or '[]')
        # enrich with product info
        out = []
        for it in items:
            p_res = await s.execute(select(Product).where(Product.id == it.get('product_id')))
            p = p_res.scalars().first()
            if p:
                out.append({
                    'product_id': p.id,
                    'name': p.name,
                    'price': p.price,
                    'qty': it.get('qty', 1)
                })
        return {"items": out}

async def clear_cart(user_id: int):
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(User).where(User.tg_id == user_id))
        user = res.scalars().first()
        if not user:
            return {"ok": True}
        res2 = await s.execute(select(Cart).where(Cart.user_id == user.id))
        cart = res2.scalars().first()
        if cart:
            cart.items_json = json.dumps([])
            cart.updated_at = datetime.utcnow()
            await s.commit()
        return {"ok": True}

async def create_order(order_data):
    async with AsyncSessionLocal() as s:
        # ensure user exists
        res = await s.execute(select(User).where(User.tg_id == order_data.tg_id))
        user = res.scalars().first()
        if not user:
            user = User(tg_id=order_data.tg_id, name=order_data.name, phone=order_data.phone)
            s.add(user)
            await s.flush()
        # if order_data.items is empty, try to load from cart
        items = getattr(order_data, 'items', None)
        if not items:
            # try cart
            res_cart = await s.execute(select(Cart).where(Cart.user_id == user.id))
            cart = res_cart.scalars().first()
            items = json.loads(cart.items_json) if cart and cart.items_json else []
        o = Order(user_id=user.id, items_json=json.dumps(items), total_price=order_data.total_price, address=order_data.address, phone=order_data.phone, payment_method=order_data.payment_method, status='new')
        s.add(o)
        await s.commit()
        await s.refresh(o)
        # clear cart after creating order
        res_c = await s.execute(select(Cart).where(Cart.user_id == user.id))
        cart = res_c.scalars().first()
        if cart:
            cart.items_json = json.dumps([])
            await s.commit()
        return o

async def mark_order_paid(order_id: int):
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Order).where(Order.id == order_id))
        o = res.scalars().first()
        if not o:
            return False
        o.status = 'paid'
        await s.commit()
        return True


async def mark_order_status(order_id: int, status: str):
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Order).where(Order.id == order_id))
        o = res.scalars().first()
        if not o:
            return False
        o.status = status
        await s.commit()
        return True


async def list_orders_all():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Order).order_by(Order.created_at.desc()))
        return res.scalars().all()


async def list_orders_by_tg_id(tg_id: int):
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(User).where(User.tg_id == tg_id))
        user = res.scalars().first()
        if not user:
            return []
        res2 = await s.execute(select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc()))
        orders = res2.scalars().all()
        return orders
