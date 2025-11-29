import os
from . import crud
import os
from aiogram import Bot

BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT = os.getenv('ADMIN_CHAT') or os.getenv('ADMIN_IDS')

def get_payment_url(order_id: int):
    # returns a simple mock payment page on backend
    return f"{BASE_URL}/pay/{order_id}"

async def process_webhook(order_id: int, status: str):
    # update order status in DB
    await crud.mark_order_status(order_id, status)

    # notify user and admin about status change
    try:
        if not BOT_TOKEN:
            return True
        bot = Bot(token=BOT_TOKEN)
        # import here to avoid circular import
        from .db import AsyncSessionLocal, Order, User
        from sqlalchemy import select
        async with AsyncSessionLocal() as s:
            res = await s.execute(select(Order).where(Order.id == order_id))
            o = res.scalars().first()
            if o:
                # find user
                res2 = await s.execute(select(User).where(User.id == o.user_id))
                u = res2.scalars().first()
                text = f"Статус заказа #{o.id} изменён: <b>{status}</b>"
                if u and getattr(u, 'tg_id', None):
                    try:
                        await bot.send_message(u.tg_id, text, parse_mode='HTML')
                    except Exception:
                        pass
                # notify admin
                if ADMIN_CHAT:
                    try:
                        await bot.send_message(int(ADMIN_CHAT), f"Admin: {text}", parse_mode='HTML')
                    except Exception:
                        pass
        # close bot session
        try:
            await bot.session.close()
        except Exception:
            pass
    except Exception:
        # don't raise errors from notifications
        pass
    return True
