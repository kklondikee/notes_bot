import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from scheduler import start_scheduler
from weather_scheduler import start_weather_scheduler
from handlers import common_router, notes_router, media_router, weather_router, admin_router, share_router  # добавили share_router

logging.basicConfig(level=logging.INFO)

async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(common_router)
    dp.include_router(notes_router)
    dp.include_router(media_router)
    dp.include_router(weather_router)
    dp.include_router(admin_router)
    dp.include_router(share_router)  # <-- добавить

    start_scheduler(bot)
    start_weather_scheduler(bot)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())