from aiogram import Router
from aiogram.types import Message, WebAppInfo, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
import httpx

import config
from bot.services.db import AsyncSessionLocal, Product, Category

router = Router()

ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
BASE_URL = os.getenv('BASE_URL', 'https://mandanator.ru')


@router.message(Command('admin'))
async def cmd_admin(message: Message):
    """Открыть админ-панель через WebApp"""
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer('❌ Доступ запрещён')
        return
    
    # Создаём кнопку с WebApp для админки
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔐 Открыть админ-панель",
        web_app=WebAppInfo(url=f"{BASE_URL}/webapp/admin.html")
    )
    
    await message.answer(
        "👨‍💼 Админ-панель Jafood\n\n"
        "Управляйте:\n"
        "• 🍔 Меню и товарами\n"
        "• 📁 Категориями\n"
        "• 📋 Заказами и статусами\n"
        "• 📊 Статистикой продаж\n\n"
        "Нажмите кнопку ниже для входа:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(lambda c: c.data and c.data.startswith('confirm_login:'))
async def callback_confirm_login(callback: CallbackQuery):
    """Подтверждение входа в админ-панель"""
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    request_id = callback.data.split(':')[1]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/admin/confirm-login/{request_id}",
                json={
                    "action": "confirm",
                    "user_data": {
                        "id": callback.from_user.id,
                        "first_name": callback.from_user.first_name,
                        "last_name": callback.from_user.last_name or "",
                        "username": callback.from_user.username or ""
                    }
                }
            )
        
        if response.status_code == 200:
            await callback.message.edit_text(
                "✅ Вход подтверждён!\n\n"
                "Пользователь может продолжить работу в админ-панели."
            )
            await callback.answer("✅ Доступ разрешён")
        else:
            await callback.answer("❌ Ошибка подтверждения", show_alert=True)
    except Exception as e:
        print(f"Error confirming login: {e}")
        await callback.answer("❌ Ошибка сервера", show_alert=True)


@router.callback_query(lambda c: c.data and c.data.startswith('reject_login:'))
async def callback_reject_login(callback: CallbackQuery):
    """Отклонение входа в админ-панель"""
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    request_id = callback.data.split(':')[1]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/admin/confirm-login/{request_id}",
                json={"action": "reject"}
            )
        
        if response.status_code == 200:
            await callback.message.edit_text(
                "❌ Вход отклонён!\n\n"
                "Попытка входа была заблокирована."
            )
            await callback.answer("❌ Доступ запрещён")
        else:
            await callback.answer("❌ Ошибка", show_alert=True)
    except Exception as e:
        print(f"Error rejecting login: {e}")
        await callback.answer("❌ Ошибка сервера", show_alert=True)


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
