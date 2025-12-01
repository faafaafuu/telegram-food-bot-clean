"""
Полнофункциональный Telegram-бот для ресторана Jafood
Поддержка: меню, корзина, оформление заказа, оплата, доставка/самовывоз
"""
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.handlers import start
from bot.handlers.menu import router as menu_router
from bot.handlers.cart import router as cart_router
from bot.handlers.order import router as order_router
from bot.handlers.admin import router as admin_router
from bot.services.db import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен в переменных окружения!")

ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def set_bot_commands():
    """Установка команд бота в меню"""
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="orders", description="📋 Мои заказы"),
        BotCommand(command="about", description="ℹ️ О ресторане"),
    ]
    
    # Добавляем команду /admin для администраторов
    if ADMIN_IDS:
        admin_commands = commands + [
            BotCommand(command="admin", description="👨‍💼 Админ-панель")
        ]
        # Устанавливаем разные команды для админов
        for admin_id in ADMIN_IDS:
            try:
                from aiogram.types import BotCommandScopeChat
                await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
            except Exception as e:
                logger.warning(f"Не удалось установить команды для админа {admin_id}: {e}")
    
    # Общие команды для всех
    await bot.set_my_commands(commands)
    logger.info("✅ Команды бота установлены")


async def on_startup():
    """Действия при запуске бота"""
    logger.info("🚀 Запуск бота...")
    await init_db()
    await set_bot_commands()
    logger.info("✅ Бот запущен и готов к работе!")


async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("🛑 Остановка бота...")
    await bot.session.close()
    logger.info("✅ Бот остановлен")


async def main():
    """Основная функция запуска бота"""
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(menu_router)
    dp.include_router(cart_router)
    dp.include_router(order_router)
    dp.include_router(admin_router)
    
    # Запуск
    try:
        await on_startup()
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await on_shutdown()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Бот остановлен пользователем")
