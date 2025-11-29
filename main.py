import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
from bot.services.db import init_db, create_sample_data
from bot.handlers import catalog, cart, order, admin

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    await create_sample_data()

    bot = Bot(token=config.BOT_TOKEN, parse_mode='HTML')
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # include routers
    dp.include_router(catalog)
    dp.include_router(cart)
    dp.include_router(order)
    dp.include_router(admin)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
