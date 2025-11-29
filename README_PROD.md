Production deployment instructions

1) Prepare environment

Create `.env` with values (if you map nginx to non-standard host ports include the port in `BASE_URL`):

```
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789
# If you use the default compose with nginx mapped to 8020 on the host:
# BASE_URL should include the port, e.g. http://194.163.141.13:8020
BASE_URL=http://your.domain.tld
```

2) Build and run (example using docker-compose prod):

```bash
cd docker
docker compose -f docker-compose.prod.yml up -d --build
```

3) TLS / HTTPS

- This compose file assumes certificates will be available under `docker/certs` and nginx will be configured to serve them.
- For automatic Let's Encrypt, use a companion container (certbot or nginx-proxy with companion). For testing you may run without TLS and expose HTTP.

4) Webhooks and bot

- The backend uses `BOT_TOKEN` to send notifications; the bot process runs separately and polls Telegram in this setup.
- For production it's recommended to use webhooks instead of polling; configure Telegram webhook to `https://your.domain.tld/bot/webhook` and implement a webhook receiver.

5) Payments (YooKassa / CloudPayments)

- We provide a mock payment flow: `/pay/{order_id}` and `POST /webhook/payment` that simulates provider webhook.
- To integrate YooKassa or CloudPayments:
  - Create account and obtain `SHOP_ID`, `SECRET_KEY` (YooKassa) or `PUBLIC_KEY`/`SECRET_KEY` (CloudPayments).
  - Implement server signatures verification per provider docs in `backend/app/payments.py`.
  - Set provider's webhook URL to `https://your.domain.tld/webhook/payment`.

6) Admin

- Admin UI is served at `/webapp/admin/index.html`.
- Secure this route via nginx/basic auth or add authentication in FastAPI (recommended).

7) Notes

- Update `DATABASE_URL` to point to `postgresql+asyncpg://user:pass@db/dbname` in environment.
- Adjust `nginx` config if you use a reverse proxy or load balancer.

