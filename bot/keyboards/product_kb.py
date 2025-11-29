from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def product_card_kb(product_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="+", callback_data=f"plus_{product_id}"),
        InlineKeyboardButton(text="Добавить", callback_data=f"add_{product_id}"),
        InlineKeyboardButton(text="-", callback_data=f"minus_{product_id}"),
    )
    builder.add(InlineKeyboardButton(text="В корзину", callback_data=f"to_cart_{product_id}"))
    return builder.as_markup()


def catalog_categories_kb(categories: list):
    builder = InlineKeyboardBuilder()
    for c in categories:
        builder.add(InlineKeyboardButton(text=c.title, callback_data=f"cat_{c.id}"))
    return builder.as_markup()


def cart_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Очистить", callback_data="clear_cart"),
        InlineKeyboardButton(text="Оформить", callback_data="checkout"),
    )
    return builder.as_markup()
