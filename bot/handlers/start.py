"""Обработчик стартовой команды и главного меню"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import os

router = Router()

# URL веб-приложения
WEBAPP_URL = os.getenv('WEBHOOK_URL') or os.getenv('BASE_URL', 'https://mandanator.ru')


def get_main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    buttons = [
        [InlineKeyboardButton(text="🍕 Открыть меню", web_app=WebAppInfo(url=f"{WEBAPP_URL}/webapp/"))],
        [InlineKeyboardButton(text="ℹ️ О ресторане", callback_data="about")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Стартовое сообщение с главным меню"""
    welcome_text = (
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"Добро пожаловать в <b>🍕 Jafood</b> — ваш любимый ресторан!\n\n"
        f"🔸 Закажите любимые блюда\n"
        f"🔸 Доставка или самовывоз\n"
        f"🔸 Наличные, карта или онлайн-оплата\n\n"
        f"Выберите действие:"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_kb())


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "about")
async def show_about(callback: CallbackQuery):
    """Информация о ресторане"""
    about_text = (
        "ℹ️ <b>О ресторане Jafood</b>\n\n"
        "🍕 Мы готовим с душой!\n\n"
        "📍 <b>Адрес:</b> г. Москва, ул. Примерная, д. 1\n"
        "⏰ <b>Режим работы:</b> 10:00 - 23:00\n"
        "📞 <b>Телефон:</b> +7 (999) 123-45-67\n\n"
        "🚚 <b>Доставка:</b> 30-60 минут\n"
        "💰 <b>Минимальный заказ:</b> 500 ₽\n"
        "🎁 <b>Акции:</b> При заказе от 1500 ₽ — бесплатная доставка!"
    )
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(about_text, reply_markup=back_kb)
    await callback.answer()


@router.message(Command("about"))
async def cmd_about(message: Message):
    """Команда /about"""
    about_text = (
        "ℹ️ <b>О ресторане Jafood</b>\n\n"
        "🍕 Мы готовим с душой!\n\n"
        "📍 <b>Адрес:</b> г. Москва, ул. Примерная, д. 1\n"
        "⏰ <b>Режим работы:</b> 10:00 - 23:00\n"
        "📞 <b>Телефон:</b> +7 (999) 123-45-67\n\n"
        "🚚 <b>Доставка:</b> 30-60 минут\n"
        "💰 <b>Минимальный заказ:</b> 500 ₽\n"
        "🎁 <b>Акции:</b> При заказе от 1500 ₽ — бесплатная доставка!"
    )
    await message.answer(about_text, reply_markup=get_main_menu_kb())
