YooKassa / CloudPayments integration notes

This project includes a mock payment flow (`/pay/{order_id}` and `POST /webhook/payment`) for development and demonstration. To integrate a real provider follow these steps.

YooKassa (Yandex.Checkout)
- Obtain credentials: `SHOP_ID` and `SECRET_KEY` from YooKassa.
- When creating payment, call YooKassa API to create a payment and store its `payment_id` in your `orders` table.
- Set the webhook URL in the YooKassa dashboard to `https://your.domain.tld/webhook/payment`.
- Verify incoming webhook signatures using the `SECRET_KEY` according to YooKassa docs (HMAC-SHA256 over body etc.).
- On successful payment, update order status to `paid` and call `payments.process_webhook(order_id, 'paid')` (or mark via internal function).

CloudPayments
- Obtain `PUBLIC_KEY` and `SECRET_KEY`.
- Use CloudPayments API to charge the card or redirect to payment page.
- Configure webhook to `https://your.domain.tld/webhook/payment` and validate `Content-MD5`/signature per provider docs.
- Upon successful verification, update the order and call `payments.process_webhook(order_id, 'paid')`.

Implementation hints
- Implement provider-specific verification in `backend/app/payments.py` inside `process_webhook` and/or a separate `verify_*` helper.
- Never trust incoming request body without validating signature.
- Use HTTPS in production and keep secrets in environment variables or a secrets manager.
- For testing without real money, use provider sandbox/test keys and test webhooks.

Mock flow in this repo
- `GET /pay/{order_id}` — demo page to simulate paying an order.
- `POST /webhook/payment` — mock webhook that accepts `{order_id, status}` and updates order.

