from datetime import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import database as db
from weather import get_weather

scheduler = AsyncIOScheduler()

async def send_morning_weather(bot: Bot):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    print(f"🌤 Запуск утренней рассылки погоды в {now}")

    users = db.get_subscribed_users()
    print(f"🕒 Запуск рассылки в {datetime.now().strftime('%H:%M:%S')}, пользователей: {len(users)}")

    for user_id, city in users:
        try:
            weather_data = await get_weather(city)
            if not weather_data:
                await bot.send_message(
                    user_id,
                    f"❌ Не удалось получить погоду для города {city}. Проверьте название города командой /setcity."
                )
                continue

            message = (
                f"🌅 *Доброе утро!* Погода на сегодня в городе{weather_data['city']}\n\n"
                f"{weather_data['icon']} {weather_data['description']}\n"
                f"🌡 Температура: {weather_data['temperature']}°C\n"
                f"↕️ В течение дня: от {weather_data['min_temp']}°C до {weather_data['max_temp']}°C\n"
                f"💧 Влажность: {weather_data['humidity']}%\n"
                f"🌬 Ветер: {weather_data['wind_speed']} м/с\n"
                f"☔ Осадки: {weather_data['precipitation']} мм\n"
                f"🌅 Восход: {weather_data['sunrise']}\n"
                f"🌇 Закат: {weather_data['sunset']}\n\n"
                f"🧥 *Совет:* {weather_data['clothing_advice']}\n\n"
                f"Хорошего дня! 🌟"
            )
            await bot.send_message(user_id, message, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка при отправке погоды пользователю {user_id}: {e}")

def start_weather_scheduler(bot: Bot):
    scheduler.add_job(
        send_morning_weather,
        trigger=CronTrigger(hour=datetime.now().hour, minute=0),  # Запуск каждый день в 7:00 МСК (UTC+3)
        args=[bot],
        id="morning_weather",
        replace_existing=True
    )
    scheduler.start()
    print("🌤 Планировщик погоды запущен, следующая рассылка в 4:00 UTC")