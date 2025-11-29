import asyncio
import json
from datetime import datetime

from bot.services.db import AsyncSessionLocal, Product, Cart, Order
from sqlalchemy import select, delete, text


TEST_USER_ID = 123456789


async def main():
    async with AsyncSessionLocal() as session:
        # Очистим корзину тестового пользователя
        await session.execute(delete(Cart).where(Cart.user_id == TEST_USER_ID))
        await session.commit()

        # Возьмем первые 2 товара из каталога
        # Запросим только нужные колонки, чтобы избежать несоответствий схемы
        raw = await session.execute(text("SELECT id, name, price FROM products LIMIT 2"))
        rows = raw.fetchall()
        if not rows:
            print("Нет товаров в базе — добавьте товары перед тестом.")
            return

        # Добавим в корзину
        for i, row in enumerate(rows, start=1):
            product_id, name, price = row
            session.add(Cart(user_id=TEST_USER_ID, product_id=product_id, qty=i))
        await session.commit()

        # Сформируем items_json и total_price
        items_json_list = []
        total_price = 0.0
        for i, row in enumerate(rows, start=1):
            product_id, name, price = row
            qty = i
            total = float(price) * qty
            total_price += total
            items_json_list.append({
                "product_id": int(product_id),
                "name": name,
                "qty": qty,
                "price": float(price),
                "total": total
            })

        order = Order(
            user_id=TEST_USER_ID,
            items_json=json.dumps(items_json_list, ensure_ascii=False),
            total_price=total_price,
            address="Тестовый адрес, ул. Пример 1",
            phone="+7 900 000-00-00",
            payment_method="cash",
            status="new",
            created_at=datetime.now(),
        )
        session.add(order)
        await session.flush()

        # Очистим корзину
        await session.execute(delete(Cart).where(Cart.user_id == TEST_USER_ID))
        await session.commit()

        print(f"Создан тестовый заказ #{order.id} на сумму {total_price} ₽")


if __name__ == "__main__":
    asyncio.run(main())
