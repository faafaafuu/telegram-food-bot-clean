import asyncio
import json
from datetime import datetime

from bot.services.db import AsyncSessionLocal, Product, Cart, Order
from sqlalchemy import select, delete


TEST_USER_ID = 123456789


async def main():
    async with AsyncSessionLocal() as session:
        # Очистим корзину тестового пользователя
        await session.execute(delete(Cart).where(Cart.user_id == TEST_USER_ID))
        await session.commit()

        # Возьмем первые 2 товара из каталога
        products_result = await session.execute(select(Product).limit(2))
        products = products_result.scalars().all()
        if not products:
            print("Нет товаров в базе — добавьте товары перед тестом.")
            return

        # Добавим в корзину
        for i, p in enumerate(products, start=1):
            session.add(Cart(user_id=TEST_USER_ID, product_id=p.id, qty=i))
        await session.commit()

        # Сформируем items_json и total_price
        items_json_list = []
        total_price = 0.0
        for i, p in enumerate(products, start=1):
            qty = i
            total = p.price * qty
            total_price += total
            items_json_list.append({
                "product_id": p.id,
                "name": p.name,
                "qty": qty,
                "price": p.price,
                "total": total
            })

        order = Order(
            user_id=TEST_USER_ID,
            items_json=json.dumps(items_json_list, ensure_ascii=False),
            total_price=total_price,
            address="Тестовый адрес, ул. Пример 1",
            name="Тест Пользователь",
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
