"""Обработчик корзины"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, delete
from bot.services.db import AsyncSessionLocal, Cart, Product

router = Router()


async def get_cart_items(user_id: int):
    """Получить товары из корзины пользователя"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Cart).where(Cart.user_id == user_id)
        )
        cart_items = result.scalars().all()
        
        if not cart_items:
            return [], 0.0
        
        items_data = []
        total = 0.0
        
        for cart_item in cart_items:
            product_result = await session.execute(
                select(Product).where(Product.id == cart_item.product_id)
            )
            product = product_result.scalar_one_or_none()
            
            if product:
                item_total = product.price * cart_item.qty
                items_data.append({
                    'product': product,
                    'qty': cart_item.qty,
                    'total': item_total
                })
                total += item_total
        
        return items_data, total


@router.message(Command("cart"))
async def cmd_cart(message: Message):
    """Показать корзину"""
    await show_cart_handler(message.from_user.id, message)


@router.callback_query(F.data == "show_cart")
async def callback_show_cart(callback: CallbackQuery):
    """Показать корзину через callback"""
    await show_cart_handler(callback.from_user.id, callback.message, edit=True)
    await callback.answer()


async def show_cart_handler(user_id: int, message: Message, edit: bool = False):
    """Универсальный обработчик отображения корзины"""
    items, total = await get_cart_items(user_id)
    
    if not items:
        text = (
            "🛒 <b>Ваша корзина пуста</b>\n\n"
            "Добавьте товары из меню, чтобы оформить заказ!"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍕 Открыть меню", callback_data="main_menu")]
        ])
    else:
        text = "🛒 <b>Ваша корзина:</b>\n\n"
        for item in items:
            text += f"• <b>{item['product'].name}</b>\n"
            text += f"  {item['qty']} шт. × {item['product'].price} ₽ = {item['total']} ₽\n\n"
        
        text += f"💰 <b>Итого: {total} ₽</b>"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="start_order")],
            [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
    
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "clear_cart")
async def clear_cart_callback(callback: CallbackQuery):
    """Очистить корзину"""
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(Cart).where(Cart.user_id == callback.from_user.id)
        )
        await session.commit()
    
    await callback.answer("🗑 Корзина очищена", show_alert=True)
    await show_cart_handler(callback.from_user.id, callback.message, edit=True)
