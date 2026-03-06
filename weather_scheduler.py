import asyncio
from datetime import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import database as db
from weather import get_weather_by_coords
import pytz

scheduler = AsyncIOScheduler()

async def send_morning_weather(bot: Bot):
    """Проверяет, у кого сейчас 7 утра, и отправляет погоду."""
    now_utc = datetime.now(pytz.UTC)
    users = db.get_subscribed_users()  # (user_id, city, timezone)

    for user_id, city, tz_str in users:
        try:
            user_tz = pytz.timezone(tz_str)
        except Exception:
            continue

        user_now = now_utc.astimezone(user_tz)
        if user_now.hour == 7 and user_now.minute == 0:
            # Отправляем погоду
            # Здесь нужно получить погоду по городу. Можно использовать get_weather_by_coords, но у нас нет координат.
            # Упрощённо: используем get_weather (город по имени). Это может быть неточно, но для демо сойдёт.
            from weather import get_weather
            weather_data, _, _ = await get_weather(city)
            if not weather_data:
                await bot.send_message(
                    user_id,
                    f"❌ Не удалось получить погоду для города {city}. Проверьте название города командой /setcity."
                )
                continue

            message = (
                f"🌅 *Доброе утро!* Погода на сегодня в {weather_data['city']}\n\n"
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

def start_weather_scheduler(bot: Bot):
    scheduler.add_job(
        send_morning_weather,
        trigger=IntervalTrigger(minutes=1),
        args=[bot],
        id="morning_weather",
        replace_existing=True
    )
    scheduler.start()
    print("🌤 Планировщик погоды запущен (проверка каждую минуту)")