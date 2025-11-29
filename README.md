# Telegram Food Bot (clean)

Простой рабочий шаблон Telegram-бота для заказа еды на `aiogram 3` + `SQLite (aiosqlite)`.

Структура:
```
/telegram-food-bot-clean
  /bot
    /handlers
      catalog.py
      cart.py
      order.py
      admin.py
    /keyboards
      product_kb.py
    /services
      db.py
      payment.py
    /utils
      helpers.py
  main.py
  config.py
  requirements.txt
```

Запуск (polling):

1. Установите зависимости:

```bash
python3 -m pip install -r requirements.txt
```

2. Создайте `.env` рядом с `config.py` или установите переменные окружения `BOT_TOKEN` и `ADMIN_IDS`.

3. Запустите:

```bash
python3 main.py
```

Webhook (кратко):
- Настройте `WEBHOOK_URL` в `.env` и реализуйте `aiohttp` сервер, который вызовет `bot.set_webhook(WEBHOOK_URL)` и будет принимать POST.

Примечания:
- Это минимальный шаблон: админ-функции упрощены (команда `/addproduct` принимает в одной строке). Можно расширять ввод через FSM.
- Онлайн оплата реализована как мок в `bot/services/payment.py`.

Если хотите, я могу:
- Добавить полноценный FSM для оформления заказа и для админ-панели (пошаговый ввод с фото).
- Добавить экспорт заказов в CSV и CRUD для категорий.
- Подготовить docker-compose с PostgreSQL.
