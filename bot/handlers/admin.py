from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

import config
from bot.services.db import AsyncSessionLocal, Product, Category

router = Router()

@router.message(Command('admin'))
async def cmd_admin(message: Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer('Доступ запрещён')
        return
    await message.answer('Админ-панель:\n/addproduct - добавить продукт (формат: name|desc|price|category|tags)\n/listproducts - список')

@router.message(Command('addproduct'))
async def cmd_addproduct(message: Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer('Доступ запрещён')
        return
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.answer('Использование: /addproduct name|desc|price|category|tags')
        return
    payload = parts[1]
    try:
        name, desc, price, category_title, tags = [x.strip() for x in payload.split('|')]
        price = float(price)
    except Exception:
        await message.answer('Неверный формат')
        return
    async with AsyncSessionLocal() as s:
        # ensure category
        cat = (await s.execute(Category.__table__.select().where(Category.title == category_title))).scalar_one_or_none()
        if not cat:
            cat = Category(title=category_title)
            s.add(cat)
            await s.flush()
        prod = Product(name=name, description=desc, price=price, category_id=cat.id, tags=tags)
        s.add(prod)
        await s.commit()
    await message.answer('Продукт добавлен')

@router.message(Command('listproducts'))
async def cmd_listproducts(message: Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer('Доступ запрещён')
        return
    async with AsyncSessionLocal() as s:
        res = (await s.execute(Product.__table__.select())).scalars().all()
        if not res:
            await message.answer('Нет товаров')
            return
        lines = [f"{p.id}. {p.name} — {p.price}₽" for p in res]
        await message.answer('\n'.join(lines))
