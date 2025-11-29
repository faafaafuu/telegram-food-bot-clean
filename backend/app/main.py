from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import HTMLResponse
import uvicorn

from . import db, crud, schemas, payments

app = FastAPI(title="Telegram Food Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the webapp static files at /webapp (resolve relative to project root)
static_dir = Path(__file__).resolve().parent.parent.parent.joinpath('webapp')
# Serve SPA: enable html=True so directory requests return index.html
app.mount("/webapp", StaticFiles(directory=str(static_dir), html=True), name="webapp")

@app.on_event("startup")
async def startup():
    await db.init_db()
    await db.create_sample_data()


@app.get("/api/categories")
async def get_categories():
    return await crud.list_categories()


@app.post('/api/admin/category')
async def api_create_category(payload: dict):
    c = await crud.create_category(payload)
    return c


@app.put('/api/admin/category/{cat_id}')
async def api_update_category(cat_id: int, payload: dict):
    c = await crud.update_category(cat_id, payload)
    if not c:
        raise HTTPException(404, 'category not found')
    return c


@app.delete('/api/admin/category/{cat_id}')
async def api_delete_category(cat_id: int):
    ok = await crud.delete_category(cat_id)
    if not ok:
        raise HTTPException(404, 'category not found')
    return {"ok": True}


@app.get("/api/products")
async def get_products(category_id: int = None):
    return await crud.list_products(category_id)


@app.post('/api/admin/product')
async def api_create_product(payload: dict):
    p = await crud.create_product(payload)
    return p


@app.put('/api/admin/product/{product_id}')
async def api_update_product(product_id: int, payload: dict):
    p = await crud.update_product(product_id, payload)
    if not p:
        raise HTTPException(404, 'product not found')
    return p


@app.delete('/api/admin/product/{product_id}')
async def api_delete_product(product_id: int):
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
    """Синхронизация корзины из WebApp"""
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
async def create_order(order: schemas.CreateOrder):
    new = await crud.create_order(order)
    # return payment URL
    pay_url = payments.get_payment_url(new.id)
    return {"order_id": new.id, "payment_url": pay_url}


@app.get("/api/orders/{tg_id}")
async def get_orders_by_tg(tg_id: int):
    return await crud.list_orders_by_tg_id(tg_id)


@app.get('/api/admin/orders')
async def admin_list_orders():
    return await crud.list_orders_all()


@app.post('/api/admin/order/{order_id}/status')
async def admin_change_status(order_id: int, payload: dict):
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
