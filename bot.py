import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from scheduler import start_scheduler
from handlers import common_router, notes_router  # подключаем только готовые роутеры

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация базы данных
    init_db()

    # Создание бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключение роутеров
    dp.include_router(common_router)
    dp.include_router(notes_router)
    # Остальные роутеры можно подключить по мере наполнения

    # Запуск планировщика напоминаний
    start_scheduler(bot)

    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())