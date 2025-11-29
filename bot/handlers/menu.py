"""Обработчик меню (интеграция с WebApp)"""
import json
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
import os
from sqlalchemy import delete
from bot.services.db import AsyncSessionLocal, Cart

router = Router()

WEBAPP_URL = os.getenv('WEBHOOK_URL') or os.getenv('BASE_URL', 'https://mandanator.ru')
@router.message(F.web_app_data)
async def handle_webapp_data(message: Message, state: FSMContext):
    """Обработка данных от WebApp (checkout)"""
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        
        if action == 'checkout':
            items = data.get('items', [])
            total = data.get('total', 0)
            
            if not items:
                await message.answer("❌ Корзина пуста!")
                return
            
            # Сохраняем данные в корзину БД
            user_id = message.from_user.id
            async with AsyncSessionLocal() as session:
                # Очищаем старую корзину
                await session.execute(delete(Cart).where(Cart.user_id == user_id))
                await session.commit()
                
                # Добавляем новые позиции
                for item in items:
                    cart_item = Cart(
                        user_id=user_id,
                        product_id=item['product_id'],
                        qty=item['qty']
                    )
                    session.add(cart_item)
                await session.commit()
            
            # Сохраняем total в state для будущего использования
            await state.update_data(checkout_total=total)
            
            # Переходим к оформлению заказа
            from bot.handlers.order import start_order
            await message.answer(
                f"✅ Товары добавлены в корзину!\n\n"
                f"💰 Сумма заказа: {total} ₽\n\n"
                f"Нажмите кнопку ниже, чтобы оформить заказ:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="start_order")]
                ])
            )
        else:
            await message.answer("Неизвестное действие от WebApp")
            
    except Exception as e:
        print(f"Error handling webapp data: {e}")
        await message.answer("❌ Ошибка обработки данных. Попробуйте еще раз.")




@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Открыть меню через WebApp"""
    menu_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍕 Открыть меню", web_app=WebAppInfo(url=f"{WEBAPP_URL}/webapp/"))],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    await message.answer(
        "📖 <b>Наше меню</b>\n\n"
        "Нажмите кнопку ниже, чтобы открыть интерактивное меню:",
        reply_markup=menu_kb
    )
