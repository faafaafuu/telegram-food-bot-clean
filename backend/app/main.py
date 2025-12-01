from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import HTMLResponse
import uvicorn
import os
import hashlib
import time
import secrets
from typing import Optional

from . import db, crud, schemas, payments

app = FastAPI(title="Telegram Food Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Защита от брутфорса
auth_attempts = {}  # {ip: [(timestamp, success), ...]}
MAX_ATTEMPTS = 20
BLOCK_TIME = 300  # 5 минут

# Хранилище токенов {token: {user_id, created_at}}
active_tokens = {}

# Хранилище запросов на вход {request_id: {username, status, timestamp, user_data}}
login_requests = {}

def check_rate_limit(ip: str):
    """Проверка на брутфорс"""
    now = time.time()
    if ip not in auth_attempts:
        auth_attempts[ip] = []
    
    # Удаляем старые попытки
    auth_attempts[ip] = [(t, s) for t, s in auth_attempts[ip] if now - t < BLOCK_TIME]
    
    # Проверяем количество неудачных попыток
    failed = [t for t, s in auth_attempts[ip] if not s]
    if len(failed) >= MAX_ATTEMPTS:
        raise HTTPException(429, f"Слишком много попыток входа. Попробуйте через {BLOCK_TIME // 60} минут")

def generate_token(user_id: int) -> str:
    """Генерация безопасного токена"""
    token = secrets.token_urlsafe(32)
    active_tokens[token] = {
        'user_id': user_id,
        'created_at': time.time()
    }
    return token

def verify_admin_token(authorization: Optional[str] = Header(None)) -> int:
    """Проверка токена администратора"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, "Требуется авторизация")
    
    token = authorization.replace('Bearer ', '')
    if token not in active_tokens:
        raise HTTPException(401, "Недействительный токен")
    
    # Проверяем срок действия (24 часа)
    token_data = active_tokens[token]
    if time.time() - token_data['created_at'] > 86400:
        del active_tokens[token]
        raise HTTPException(401, "Токен истёк")
    
    return token_data['user_id']

# Mount the webapp static files at /webapp (resolve relative to project root)
static_dir = Path(__file__).resolve().parent.parent.parent.joinpath('webapp')
# Serve SPA: enable html=True so directory requests return index.html
app.mount("/webapp", StaticFiles(directory=str(static_dir), html=True), name="webapp")

@app.on_event("startup")
async def startup():
    await db.init_db()
    await db.create_sample_data()


@app.post("/api/admin/auth")
async def admin_auth(request: Request, payload: dict):
    """Авторизация администратора через Telegram или логин/пароль"""
    client_ip = request.client.host
    check_rate_limit(client_ip)
    
    auth_type = payload.get('auth_type', 'telegram')  # telegram или password
    
    if auth_type == 'password':
        # Авторизация по логину/паролю
        username = payload.get('username')
        password = payload.get('password')
        
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin')
        
        if not username or not password:
            auth_attempts[client_ip].append((time.time(), False))
            raise HTTPException(400, "Не указан логин или пароль")
        
        if username != admin_username or password != admin_password:
            auth_attempts[client_ip].append((time.time(), False))
            raise HTTPException(403, "Неверный логин или пароль")
        
        # Успешная аутентификация
        auth_attempts[client_ip].append((time.time(), True))
        token = generate_token(0)  # используем 0 как user_id для пароль-авторизации
        
        return {
            'success': True,
            'token': token,
            'user': {
                'id': 0,
                'first_name': 'Администратор',
                'last_name': '',
                'username': username
            }
        }
    
    else:
        # Авторизация через Telegram
        user_id = payload.get('user_id')
        username = payload.get('username')
        
        if not user_id and not username:
            auth_attempts[client_ip].append((time.time(), False))
            raise HTTPException(400, "Не указан user_id или username")
        
        # Получаем список админов из переменных окружения
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        admin_ids = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
        
        admin_usernames_str = os.getenv('ADMIN_USERNAMES', '')
        admin_usernames = [u.strip().lower().replace('@', '') for u in admin_usernames_str.split(',') if u.strip()]
        
        if not admin_ids and not admin_usernames:
            raise HTTPException(500, "Не настроены администраторы")
        
        # Проверяем по ID или username
        is_admin = False
        if user_id and user_id in admin_ids:
            is_admin = True
        elif username and username.lower().replace('@', '') in admin_usernames:
            is_admin = True
        
        if not is_admin:
            auth_attempts[client_ip].append((time.time(), False))
            raise HTTPException(403, "Доступ запрещён")
        
        # Успешная аутентификация
        auth_attempts[client_ip].append((time.time(), True))
        token = generate_token(user_id)
        
        return {
            'success': True,
            'token': token,
            'user': {
                'id': user_id,
                'first_name': payload.get('first_name', 'Админ'),
                'last_name': payload.get('last_name', ''),
                'username': payload.get('username', '')
            }
        }


@app.post("/api/admin/login")
async def admin_login(request: Request, payload: dict):
    """Прямая авторизация по логину/паролю без подтверждения"""
    client_ip = request.client.host
    check_rate_limit(client_ip)
    
    username = payload.get('username')
    password = payload.get('password')
    
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin')
    
    if not username or not password:
        auth_attempts[client_ip].append((time.time(), False))
        raise HTTPException(400, "Не указан логин или пароль")
    
    if username != admin_username or password != admin_password:
        auth_attempts[client_ip].append((time.time(), False))
        raise HTTPException(403, "Неверный логин или пароль")
    
    # Успешная авторизация
    auth_attempts[client_ip].append((time.time(), True))
    token = generate_token(0)
    
    return {
        'success': True,
        'token': token,
        'user': {
            'id': 0,
            'first_name': 'Администратор',
            'last_name': '',
            'username': username
        }
    }


@app.get("/api/admin/check-login/{request_id}")
async def check_login(request_id: str):
    """Проверка статуса запроса на вход"""
    if request_id not in login_requests:
        raise HTTPException(404, "Запрос не найден")
    
    req = login_requests[request_id]
    
    # Проверяем срок действия (5 минут)
    if time.time() - req['timestamp'] > 300:
        req['status'] = 'expired'
        return {'status': 'expired'}
    
    if req['status'] == 'confirmed':
        # Генерируем токен
        token = generate_token(0)  # используем 0 для админа по логину/паролю
        user_data = req.get('user_data') or {
            'id': 0,
            'first_name': 'Администратор',
            'last_name': '',
            'username': req['username']
        }
        
        # Удаляем запрос
        del login_requests[request_id]
        
        return {
            'status': 'confirmed',
            'token': token,
            'user': user_data
        }
    
    return {'status': req['status']}


@app.post("/api/admin/confirm-login/{request_id}")
async def confirm_login(request_id: str, payload: dict):
    """Подтверждение/отклонение запроса на вход (вызывается из callback бота)"""
    if request_id not in login_requests:
        raise HTTPException(404, "Запрос не найден")
    
    action = payload.get('action')  # 'confirm' или 'reject'
    
    if action == 'confirm':
        login_requests[request_id]['status'] = 'confirmed'
        login_requests[request_id]['user_data'] = payload.get('user_data')
    else:
        login_requests[request_id]['status'] = 'rejected'
    
    return {'success': True}


@app.get("/api/categories")
async def get_categories():
    return await crud.list_categories()


@app.post('/api/admin/category')
async def api_create_category(payload: dict, user_id: int = Depends(verify_admin_token)):
    c = await crud.create_category(payload)
    return c


@app.put('/api/admin/category/{cat_id}')
async def api_update_category(cat_id: int, payload: dict, user_id: int = Depends(verify_admin_token)):
    c = await crud.update_category(cat_id, payload)
    if not c:
        raise HTTPException(404, 'category not found')
    return c


@app.delete('/api/admin/category/{cat_id}')
async def api_delete_category(cat_id: int, user_id: int = Depends(verify_admin_token)):
    ok = await crud.delete_category(cat_id)
    if not ok:
        raise HTTPException(404, 'category not found')
    return {"ok": True}


@app.get("/api/products")
async def get_products(category_id: int = None):
    return await crud.list_products(category_id)


@app.post('/api/admin/product')
async def api_create_product(payload: dict, user_id: int = Depends(verify_admin_token)):
    p = await crud.create_product(payload)
    return p


@app.put('/api/admin/product/{product_id}')
async def api_update_product(product_id: int, payload: dict, user_id: int = Depends(verify_admin_token)):
    p = await crud.update_product(product_id, payload)
    if not p:
        raise HTTPException(404, 'product not found')
    return p


@app.delete('/api/admin/product/{product_id}')
async def api_delete_product(product_id: int, user_id: int = Depends(verify_admin_token)):
    ok = await crud.delete_product(product_id)
    if not ok:
        raise HTTPException(404, 'product not found')
    return {"ok": True}


@app.get('/api/admin/products/export')
async def export_products():
    csv = await crud.export_products_csv()
    return HTMLResponse(content=csv, media_type='text/csv')


@app.post("/api/cart/{user_id}/add")
async def add_to_cart(user_id: int, item: schemas.AddCartItem):
    return await crud.add_to_cart(user_id, item.product_id, item.qty)

@app.post("/api/cart")
async def sync_cart(request: Request):
    """Синхронизация корзины из WebApp (не используется, все в WebApp)"""
    data = await request.json()
    user_id = data.get('user_id', 0)
    items = data.get('items', [])
    
    if not user_id:
        raise HTTPException(400, "user_id required")
    
    # Очищаем старую корзину
    await crud.clear_cart(user_id)
    
    # Добавляем новые позиции
    for item in items:
        await crud.add_to_cart(user_id, item['product_id'], item['qty'])
    
    return {"ok": True}


@app.get("/api/cart/{user_id}")
async def get_cart(user_id: int):
    return await crud.get_cart(user_id)


@app.delete("/api/cart/{user_id}")
async def delete_cart(user_id: int):
    return await crud.clear_cart(user_id)


@app.post("/api/orders")
async def create_order(request: Request):
    """Создание заказа из WebApp"""
    import httpx
    import os
    import json as json_lib
    
    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(400, f"Invalid JSON: {str(e)}")
    
    user_id = data.get('user_id')
    username = data.get('username')
    first_name = data.get('first_name', 'Гость')
    items = data.get('items', [])
    total_price = data.get('total_price', 0)
    address = data.get('address', '')
    phone = data.get('phone', '')
    comment = data.get('comment', '')
    payment_method = data.get('payment_method', 'cash')
    delivery_type = data.get('delivery_type', 'delivery')
    
    # Валидация - теперь user_id необязателен
    if not items:
        raise HTTPException(400, "items are required")
    
    if not phone:
        raise HTTPException(400, "phone is required")
    
    # Создаём идентификатор клиента
    customer_identifier = f"@{username}" if username else f"ID:{user_id}" if user_id else phone
    
    # Создаем заказ в БД
    from sqlalchemy import insert
    from backend.app.db import AsyncSessionLocal, Order
    
    items_json = json_lib.dumps(items, ensure_ascii=False)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            insert(Order).values(
                user_id=user_id,
                items_json=items_json,
                total_price=total_price,
                address=address,
                phone=phone,
                payment_method=payment_method,
                status='new'
            ).returning(Order.id)
        )
        await session.commit()
        order_id = result.scalar()
    
    # Отправляем уведомление в Telegram
    bot_token = os.getenv('BOT_TOKEN')
    if bot_token and user_id:
        try:
            delivery_emoji = '🚗' if delivery_type == 'delivery' else '🏃'
            delivery_text = 'Доставка' if delivery_type == 'delivery' else 'Самовывоз'
            
            payment_texts = {
                'cash': '💵 Наличными',
                'card': '💳 Картой курьеру',
                'online': '🌐 Онлайн (ЮКасса)'
            }
            payment_text = payment_texts.get(payment_method, payment_method)
            
            items_text = '\n'.join([f"• {item['name']} × {item['qty']} = {item['price'] * item['qty']} ₽" for item in items])
            
            message = f"""
🎉 <b>Заказ #{order_id} принят!</b>

<b>Товары:</b>
{items_text}

💰 <b>Итого: {total_price} ₽</b>

{delivery_emoji} <b>{delivery_text}</b>
"""
            
            if delivery_type == 'delivery':
                message += f"📍 Адрес: {address}\n"
            
            message += f"""📱 Телефон: {phone}
💳 Оплата: {payment_text}
"""
            
            if comment:
                message += f"💬 Комментарий: {comment}\n"
            
            message += f"\n⏱ Статус: <b>Готовится</b>"
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f'https://api.telegram.org/bot{bot_token}/sendMessage',
                    json={
                        'chat_id': user_id,
                        'text': message,
                        'parse_mode': 'HTML'
                    }
                )
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    return {"ok": True, "order_id": order_id}


@app.get("/api/orders/{tg_id}")
async def get_orders_by_tg(tg_id: int):
    return await crud.list_orders_by_tg_id(tg_id)


@app.get('/api/admin/orders')
async def admin_list_orders(user_id: int = Depends(verify_admin_token)):
    return await crud.list_orders_all()


@app.post('/api/admin/order/{order_id}/status')
async def admin_change_status(order_id: int, payload: dict, user_id: int = Depends(verify_admin_token)):
    # payload: {"status": "ready"}
    status = payload.get('status')
    if not status:
        raise HTTPException(400, 'status required')
    # update DB and notify via payments.notify
    from . import payments
    await payments.process_webhook(order_id, status)
    return {"ok": True}


@app.post("/webhook/payment")
async def payment_webhook(payload: dict):
    # mocked webhook
    order_id = payload.get("order_id")
    status = payload.get("status")
    if not order_id:
        raise HTTPException(400, "order_id required")
    await payments.process_webhook(order_id, status)
    return {"ok": True}


@app.get("/pay/{order_id}", response_class=HTMLResponse)
async def pay_page(order_id: int):
    # Very simple payment page that posts to webhook to simulate payment
    html = f"""
    <html><head><meta charset='utf-8'><title>Оплата заказа {order_id}</title></head>
    <body>
      <h2>Mock Payment for order {order_id}</h2>
      <p>Click to simulate successful payment.</p>
      <button onclick="fetch('/webhook/payment', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{order_id:{order_id},status:'paid'}})}}).then(()=>alert('Payment simulated'))">Оплатить</button>
    </body></html>
    """
    return HTMLResponse(content=html)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
