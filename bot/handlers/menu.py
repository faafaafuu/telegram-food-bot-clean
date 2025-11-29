"""Обработчик меню (интеграция с WebApp)"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import os

router = Router()

WEBAPP_URL = os.getenv('WEBHOOK_URL') or os.getenv('BASE_URL', 'https://mandanator.ru')


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
