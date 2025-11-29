from typing import Dict, Any, List
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.db import Product, Category


class MenuUI:
    """Manage a single 'menu window' per chat by editing one message.

    This keeps menu and product navigation inside one message similar to
    the reference site: categories on top, product grid, product card,
    cart and checkout views — all implemented by editing a stored
    message_id for the chat.
    """

    def __init__(self):
        # chat_id -> dict(message_id=int, state=str, extras={})
        self._menus: Dict[int, Dict[str, Any]] = {}

    async def open_menu(self, bot: Bot, chat_id: int, categories: List[Category]):
        text = "<b>Меню</b>\nВыберите категорию сверху"
        kb = InlineKeyboardBuilder()
        # categories as top row buttons
        for c in categories:
            kb.add(InlineKeyboardButton(text=c.title, callback_data=f"menu:cat:{c.id}"))
        kb.add(InlineKeyboardButton(text="Корзина", callback_data="menu:cart"))
        markup = kb.as_markup(row_width=3)
        msg: Message = await bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
        self._menus[chat_id] = {"message_id": msg.message_id, "state": "menu", "category": None}

    async def show_category(self, bot: Bot, chat_id: int, category: Category, products: List[Product]):
        # Build a product grid as text + keyboard with product buttons in 2 columns
        lines = [f"<b>{category.title}</b>\nВыберите товар:"]
        for p in products:
            lines.append(f"{p.name} — {p.price}₽")
        text = "\n".join(lines)

        kb = InlineKeyboardBuilder()
        for p in products:
            kb.add(InlineKeyboardButton(text=f"{p.name} — {int(p.price)}₽", callback_data=f"menu:view:{p.id}"))
        # navigation
        kb.add(InlineKeyboardButton(text="Назад к категориям", callback_data="menu:back"))
        kb.add(InlineKeyboardButton(text="Корзина", callback_data="menu:cart"))

        menu = self._menus.get(chat_id)
        if not menu:
            # fallback: send new message
            msg = await bot.send_message(chat_id, text, reply_markup=kb.as_markup(row_width=2), parse_mode="HTML")
            self._menus[chat_id] = {"message_id": msg.message_id, "state": "category", "category": category.id}
            return

        await bot.edit_message_text(chat_id=chat_id, message_id=menu["message_id"], text=text, reply_markup=kb.as_markup(row_width=2), parse_mode="HTML")
        menu["state"] = "category"
        menu["category"] = category.id

    async def show_product(self, bot: Bot, chat_id: int, product: Product):
        # Show product photo if available, else edit text
        text = f"<b>{product.name}</b>\n{product.description}\nЦена: {product.price}₽\nРейтинг: {product.rating}\n{product.tags}"
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(text="+", callback_data=f"menu:plus:{product.id}"),
            InlineKeyboardButton(text="Добавить", callback_data=f"menu:add:{product.id}"),
            InlineKeyboardButton(text="-", callback_data=f"menu:minus:{product.id}"),
        )
        kb.add(InlineKeyboardButton(text="В корзину", callback_data=f"menu:to_cart:{product.id}"))
        kb.add(InlineKeyboardButton(text="Назад к категории", callback_data="menu:back"))

        menu = self._menus.get(chat_id)
        if not menu:
            msg = await bot.send_message(chat_id, text, reply_markup=kb.as_markup(), parse_mode="HTML")
            self._menus[chat_id] = {"message_id": msg.message_id, "state": "product", "product": product.id}
            return

        # If product has image, try editing media; otherwise edit text
        try:
            if product.image_url:
                from aiogram.types import InputMediaPhoto
                media = InputMediaPhoto(media=product.image_url, caption=text, parse_mode="HTML")
                await bot.edit_message_media(media=media, chat_id=chat_id, message_id=menu["message_id"], reply_markup=kb.as_markup())
            else:
                await bot.edit_message_text(chat_id=chat_id, message_id=menu["message_id"], text=text, reply_markup=kb.as_markup(), parse_mode="HTML")
        except Exception:
            # fallback to editing text if media edit fails
            await bot.edit_message_text(chat_id=chat_id, message_id=menu["message_id"], text=text, reply_markup=kb.as_markup(), parse_mode="HTML")

        menu["state"] = "product"
        menu["product"] = product.id

    async def show_cart(self, bot: Bot, chat_id: int, items_text: str, total: float):
        text = f"<b>Корзина</b>\n{items_text}\n\nИтого: {total}₽"
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(text="Очистить", callback_data="menu:clear_cart"),
            InlineKeyboardButton(text="Оформить", callback_data="menu:checkout"),
        )
        kb.add(InlineKeyboardButton(text="Назад к категориям", callback_data="menu:back"))

        menu = self._menus.get(chat_id)
        if not menu:
            msg = await bot.send_message(chat_id, text, reply_markup=kb.as_markup(), parse_mode="HTML")
            self._menus[chat_id] = {"message_id": msg.message_id, "state": "cart"}
            return

        await bot.edit_message_text(chat_id=chat_id, message_id=menu["message_id"], text=text, reply_markup=kb.as_markup(), parse_mode="HTML")
        menu["state"] = "cart"

    async def back_to_menu(self, bot: Bot, chat_id: int, categories: List[Category]):
        # Re-open categories view by editing the same message
        text = "<b>Меню</b>\nВыберите категорию сверху"
        kb = InlineKeyboardBuilder()
        for c in categories:
            kb.add(InlineKeyboardButton(text=c.title, callback_data=f"menu:cat:{c.id}"))
        kb.add(InlineKeyboardButton(text="Корзина", callback_data="menu:cart"))

        menu = self._menus.get(chat_id)
        if not menu:
            msg = await bot.send_message(chat_id, text, reply_markup=kb.as_markup(row_width=3), parse_mode="HTML")
            self._menus[chat_id] = {"message_id": msg.message_id, "state": "menu"}
            return

        await bot.edit_message_text(chat_id=chat_id, message_id=menu["message_id"], text=text, reply_markup=kb.as_markup(row_width=3), parse_mode="HTML")
        menu["state"] = "menu"


# Singleton UI instance
menu_ui = MenuUI()
