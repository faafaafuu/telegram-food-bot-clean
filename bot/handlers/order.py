"""Обработчик оформления заказов"""
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, delete
from datetime import datetime
from bot.services.db import AsyncSessionLocal, Cart, Product, Order

router = Router()


class OrderStates(StatesGroup):
    """Состояния оформления заказа"""
    entering_name = State()
    entering_address = State()
    entering_phone = State()
    choosing_payment = State()
    confirming = State()


@router.callback_query(F.data == "start_order")
async def start_order(callback: CallbackQuery, state: FSMContext):
    """Начать оформление заказа"""
    # Проверяем что корзина не пуста
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Cart).where(Cart.user_id == callback.from_user.id)
        )
        cart_items = result.scalars().all()
        
        if not cart_items:
            await callback.answer("❌ Корзина пуста!", show_alert=True)
            return
    
    await callback.message.edit_text(
        "👤 <b>Ваше имя</b>\n\n"
        "Напишите, пожалуйста, как к вам обращаться."
    )
    await state.set_state(OrderStates.entering_name)
    await callback.answer()

@router.message(StateFilter(OrderStates.entering_name))
async def enter_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "📍 <b>Адрес доставки</b>\n\n"
        "Укажите полный адрес доставки:\n"
        "• Улица, дом, квартира\n"
        "• Подъезд, этаж, домофон"
    )
    await state.set_state(OrderStates.entering_address)


@router.message(StateFilter(OrderStates.entering_address))
async def enter_address(message: Message, state: FSMContext):
    """Ввод адреса доставки"""
    await state.update_data(address=message.text)
    
    await message.answer(
        "📱 <b>Контактный телефон</b>\n\n"
        "Укажите номер телефона для связи:\n"
        "Формат: +7 (XXX) XXX-XX-XX"
    )
    await state.set_state(OrderStates.entering_phone)


@router.message(StateFilter(OrderStates.entering_phone))
async def enter_phone(message: Message, state: FSMContext):
    """Ввод телефона"""
    await state.update_data(phone=message.text)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Наличными", callback_data="payment_cash")],
        [InlineKeyboardButton(text="💳 Картой курьеру", callback_data="payment_card_courier")],
        [InlineKeyboardButton(text="🌐 Онлайн оплата", callback_data="payment_online")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel_order")]
    ])
    
    await message.answer(
        "💰 <b>Способ оплаты:</b>\n\n"
        "Выберите удобный способ оплаты:",
        reply_markup=kb
    )
    await state.set_state(OrderStates.choosing_payment)


@router.callback_query(StateFilter(OrderStates.choosing_payment), F.data.startswith("payment_"))
async def choose_payment(callback: CallbackQuery, state: FSMContext):
    """Выбор способа оплаты"""
    payment_type = callback.data.replace("payment_", "")
    await state.update_data(payment_method=payment_type)
    
    # Получаем данные заказа
    data = await state.get_data()
    
    # Получаем товары из корзины
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Cart).where(Cart.user_id == callback.from_user.id)
        )
        cart_items = result.scalars().all()
        
        items_text = ""
        total = 0.0
        
        for cart_item in cart_items:
            product_result = await session.execute(
                select(Product).where(Product.id == cart_item.product_id)
            )
            product = product_result.scalar_one_or_none()
            
            if product:
                item_total = product.price * cart_item.qty
                items_text += f"• {product.name} × {cart_item.qty} = {item_total} ₽\n"
                total += item_total
    
    await state.update_data(total=total)
    
    # Формируем текст подтверждения
    payment_texts = {
        'cash': '💵 Наличными',
        'card_courier': '💳 Картой курьеру',
        'online': '🌐 Онлайн оплата'
    }
    payment_text = payment_texts.get(payment_type, payment_type)
    
    confirmation_text = (
        "✅ <b>Подтверждение заказа</b>\n\n"
        f"<b>Товары:</b>\n{items_text}\n"
        f"💰 <b>Итого: {total} ₽</b>\n\n"
        f"<b>Адрес:</b> {data['address']}\n"
        f"<b>Имя:</b> {data['name']}\n"
        f"<b>Телефон:</b> {data['phone']}\n"
        f"<b>Оплата:</b> {payment_text}\n\n"
        "Подтвердите оформление заказа:"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")]
    ])
    
    await callback.message.edit_text(confirmation_text, reply_markup=kb)
    await state.set_state(OrderStates.confirming)
    await callback.answer()


@router.callback_query(StateFilter(OrderStates.confirming), F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание заказа"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    async with AsyncSessionLocal() as session:
        # Формируем JSON позиций заказа
        items_json_list = []
        result = await session.execute(select(Cart).where(Cart.user_id == user_id))
        cart_items = result.scalars().all()
        for cart_item in cart_items:
            product_result = await session.execute(select(Product).where(Product.id == cart_item.product_id))
            product = product_result.scalar_one_or_none()
            if product:
                items_json_list.append({
                    "product_id": product.id,
                    "name": product.name,
                    "qty": cart_item.qty,
                    "price": product.price,
                    "total": product.price * cart_item.qty
                })

        # Создаем заказ
        new_order = Order(
            user_id=user_id,
            items_json=json.dumps(items_json_list, ensure_ascii=False),
            total_price=data['total'],
            address=data['address'],
            name=data['name'],
            phone=data['phone'],
            payment_method=data['payment_method'],
            status='new',
            created_at=datetime.now()
        )
        session.add(new_order)
        await session.flush()

        # Очищаем корзину
        await session.execute(
            delete(Cart).where(Cart.user_id == user_id)
        )
        
        await session.commit()
        order_number = new_order.id
    
    await callback.message.edit_text(
        f"🎉 <b>Заказ #{order_number} успешно оформлен!</b>\n\n"
        "Спасибо за ваш заказ! Мы свяжемся с вами в ближайшее время.\n\n"
        f"Сумма заказа: {data['total']} ₽\n"
        f"Адрес: {data['address']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
    )
    
    await state.clear()
    await callback.answer("✅ Заказ оформлен!", show_alert=True)


@router.callback_query(StateFilter("*"), F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Отмена оформления заказа"""
    await state.clear()
    await callback.answer("❌ Оформление отменено")
    
    # Возвращаемся к корзине
    from bot.handlers.cart import show_cart_handler
    await show_cart_handler(callback.from_user.id, callback.message, edit=True)


@router.message(Command("orders"))
async def cmd_orders(message: Message):
    """Показать историю заказов"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order)
            .where(Order.user_id == message.from_user.id)
            .order_by(Order.created_at.desc())
            .limit(10)
        )
        orders = result.scalars().all()
        
        if not orders:
            await message.answer(
                "📋 <b>История заказов пуста</b>\n\n"
                "Вы еще не оформляли заказы.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🍕 Открыть меню", callback_data="main_menu")]
                ])
            )
            return
        
        text = "📋 <b>Ваши заказы:</b>\n\n"
        
        status_emoji = {
            'new': '🆕',
            'processing': '⏳',
            'delivering': '🚚',
            'completed': '✅',
            'cancelled': '❌'
        }
        
        for order in orders:
            emoji = status_emoji.get(order.status, '📦')
            date = order.created_at.strftime("%d.%m.%Y %H:%M")
            text += f"{emoji} <b>Заказ #{order.id}</b>\n"
            text += f"   Дата: {date}\n"
            text += f"   Сумма: {order.total} ₽\n"
            text += f"   Статус: {order.status}\n\n"
        
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
            ])
        )


@router.callback_query(F.data == "my_orders")
async def callback_orders(callback: CallbackQuery):
    """Показать заказы через callback"""
    await cmd_orders(callback.message)
    await callback.answer()
