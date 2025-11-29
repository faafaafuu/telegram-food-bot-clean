from aiogram import Router
from aiogram.types import Message
from aiogram import F
from aiogram import Bot
from aiogram.filters import Command

from sqlalchemy import select
from bot.services.db import AsyncSessionLocal, init_db, create_sample_data, Product, Category
from bot.services.menu_ui import menu_ui

router = Router()


@router.message(Command('start'))
async def cmd_start(message: Message):
    await message.answer("Добро пожаловать! Используйте /menu для просмотра меню.")


@router.message(Command('menu'))
async def cmd_menu(message: Message):
    # open the single-window menu
    async with AsyncSessionLocal() as s:
        result = await s.execute(select(Category))
        cats = result.scalars().all()
        if not cats:
            await create_sample_data()
            result = await s.execute(select(Category))
            cats = result.scalars().all()
    await menu_ui.open_menu(message.bot, message.chat.id, cats)


@router.callback_query(lambda c: c.data and c.data.startswith('menu:'))
async def menu_callbacks(cb):
    # Handle menu namespace callbacks: menu:cat:<id>, menu:view:<id>, menu:back, menu:cart, menu:add:<id>, menu:to_cart:<id>
    data = cb.data.split(':')
    action = data[1]
    chat_id = cb.message.chat.id
    if action == 'cat':
        cat_id = int(data[2])
        async with AsyncSessionLocal() as s:
            res = (await s.execute(select(Category).where(Category.id == cat_id))).scalar_one_or_none()
            prods = (await s.execute(select(Product).where(Product.category_id == cat_id))).scalars().all()
        if res:
            await menu_ui.show_category(cb.bot, chat_id, res, prods)
    elif action == 'view':
        pid = int(data[2])
        async with AsyncSessionLocal() as s:
            p = (await s.execute(select(Product).where(Product.id == pid))).scalar_one_or_none()
        if p:
            await menu_ui.show_product(cb.bot, chat_id, p)
    elif action == 'back':
        async with AsyncSessionLocal() as s:
            cats = (await s.execute(select(Category))).scalars().all()
        await menu_ui.back_to_menu(cb.bot, chat_id, cats)
    elif action == 'cart':
        # show simple cart via menu_ui (collect carts from DB)
        from bot.services.db import Cart
        async with AsyncSessionLocal() as s:
            rows = (await s.execute(select(Cart).where(Cart.user_id == cb.from_user.id))).scalars().all()
            if not rows:
                await menu_ui.show_cart(cb.bot, chat_id, "(пусто)", 0.0)
                return
            items = []
            total = 0.0
            for r in rows:
                prod = (await s.execute(select(Product).where(Product.id == r.product_id))).scalar_one()
                items.append(f"{prod.name} x{r.qty} — {prod.price * r.qty}₽")
                total += prod.price * r.qty
        await menu_ui.show_cart(cb.bot, chat_id, "\n".join(items), total)
    elif action in ('add', 'to_cart'):
        pid = int(data[2])
        from bot.services.db import Cart
        async with AsyncSessionLocal() as s:
            item = Cart(user_id=cb.from_user.id, product_id=pid, qty=1)
            s.add(item)
            await s.commit()
        await cb.answer('Добавлено в корзину')
    elif action in ('plus', 'minus'):
        # simple placeholder: inform user (implementation can change qty in DB)
        await cb.answer('Изменение количества (в демо не реализовано)')
