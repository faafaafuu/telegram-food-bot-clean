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
    """Обработка изменения статуса заказа и отправка уведомлений"""
    # update order status in DB
    await crud.mark_order_status(order_id, status)

    # notify user and admin about status change
    try:
        if not BOT_TOKEN:
            return True
        bot = Bot(token=BOT_TOKEN)
        
        from .db import AsyncSessionLocal, Order
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as s:
            res = await s.execute(select(Order).where(Order.id == order_id))
            o = res.scalars().first()
            
            if o:
                # Формируем сообщение о статусе
                status_texts = {
                    'new': '🆕 Новый',
                    'preparing': '👨‍🍳 Готовится',
                    'ready': '✅ Готов',
                    'delivering': '🚗 Доставляется',
                    'completed': '🎉 Завершён',
                    'cancelled': '❌ Отменён',
                    'paid': '💳 Оплачен'
                }
                status_text = status_texts.get(status, status)
                text = f"📦 Статус заказа <b>#{o.id}</b> изменён:\n{status_text}"
                
                # Отправляем уведомление клиенту (если есть user_id)
                if o.user_id:
                    try:
                        await bot.send_message(o.user_id, text, parse_mode='HTML')
                    except Exception as e:
                        print(f"Error sending notification to user {o.user_id}: {e}")
                
                # Отправляем уведомление админам
                admin_ids_str = os.getenv('ADMIN_IDS', '')
                if admin_ids_str:
                    admin_ids = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
                    for admin_id in admin_ids:
                        try:
                            await bot.send_message(admin_id, f"🔔 Admin: {text}", parse_mode='HTML')
                        except Exception as e:
                            print(f"Error sending notification to admin {admin_id}: {e}")
        
        # close bot session
        try:
            await bot.session.close()
        except Exception:
            pass
    except Exception as e:
        print(f"Error in process_webhook: {e}")
        pass
    
    return True
