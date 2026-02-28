from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import database as db
from weather import get_weather

router = Router()

# -------------------------------------------------------------------
# Команды
# -------------------------------------------------------------------
@router.message(Command("setcity"))
async def set_city(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Введите название города после команды, например:\n/setcity Москва")
        return

    city = args[1].strip()
    weather_data = await get_weather(city)
    if not weather_data:
        await message.answer("❌ Город не найден. Проверьте название и попробуйте снова.")
        return

    db.set_user_city(message.from_user.id, city)
    await message.answer(
        f"✅ Город {weather_data['city']} сохранён! Теперь вы будете получать погоду каждое утро в 7:00.\n\n"
        f"Текущая погода:\n{weather_data['icon']} {weather_data['description']}\n"
        f"🌡 {weather_data['temperature']}°C, ветер {weather_data['wind_speed']} м/с"
    )

@router.message(Command("mycity"))
async def my_city(message: Message):
    city = db.get_user_city(message.from_user.id)
    if city:
        await message.answer(f"🏙 Ваш текущий город: {city}")
    else:
        await message.answer("❌ Город не установлен. Используйте /setcity для настройки.")

@router.message(Command("weather"))
async def weather_now(message: Message):
    city = db.get_user_city(message.from_user.id)
    if not city:
        await message.answer("❌ Сначала установите город через /setcity")
        return

    status_msg = await message.answer("🌤 Получаю данные о погоде...")
    weather_data = await get_weather(city)

    if not weather_data:
        await status_msg.edit_text("❌ Не удалось получить погоду. Попробуйте позже.")
        return

    text = (
        f"🌍 *Погода в {weather_data['city']}*\n\n"
        f"{weather_data['icon']} {weather_data['description']}\n"
        f"🌡 Сейчас: {weather_data['temperature']}°C\n"
        f"↕️ В течение дня: от {weather_data['min_temp']}°C до {weather_data['max_temp']}°C\n"
        f"💧 Влажность: {weather_data['humidity']}%\n"
        f"🌬 Ветер: {weather_data['wind_speed']} м/с\n"
        f"☔ Осадки: {weather_data['precipitation']} мм\n"
        f"🌅 Восход: {weather_data['sunrise']}\n"
        f"🌇 Закат: {weather_data['sunset']}\n\n"
        f"🧥 *Совет:* {weather_data['clothing_advice']}"
    )
    await status_msg.edit_text(text, parse_mode="Markdown")

@router.message(Command("unsetcity"))
async def unset_city(message: Message):
    db.unsubscribe_user(message.from_user.id)
    await message.answer("✅ Вы отписаны от утренней рассылки погоды. Чтобы подписаться снова, используйте /setcity.")

# -------------------------------------------------------------------
# Обработчики инлайн-кнопок для погоды (с защитой от устаревших callback)
# -------------------------------------------------------------------
@router.callback_query(F.data == "weather_now")
async def weather_now_callback(callback: CallbackQuery):
    city = db.get_user_city(callback.from_user.id)
    if not city:
        await callback.message.edit_text(
            "❌ Сначала установите город через /setcity или нажмите «📍 Установить город»."
        )
        await safe_answer(callback)
        return

    await callback.message.edit_text("🌤 Получаю данные о погоде...")
    weather_data = await get_weather(city)

    if not weather_data:
        await callback.message.edit_text("❌ Не удалось получить погоду. Попробуйте позже.")
        await safe_answer(callback)
        return

    text = (
        f"🌍 *Погода в {weather_data['city']}*\n\n"
        f"{weather_data['icon']} {weather_data['description']}\n"
        f"🌡 Сейчас: {weather_data['temperature']}°C\n"
        f"↕️ В течение дня: от {weather_data['min_temp']}°C до {weather_data['max_temp']}°C\n"
        f"💧 Влажность: {weather_data['humidity']}%\n"
        f"🌬 Ветер: {weather_data['wind_speed']} м/с\n"
        f"☔ Осадки: {weather_data['precipitation']} мм\n"
        f"🌅 Восход: {weather_data['sunrise']}\n"
        f"🌇 Закат: {weather_data['sunset']}\n\n"
        f"🧥 *Совет:* {weather_data['clothing_advice']}"
    )
    await callback.message.edit_text(text, parse_mode="Markdown")
    await safe_answer(callback)

@router.callback_query(F.data == "weather_mycity")
async def weather_mycity_callback(callback: CallbackQuery):
    city = db.get_user_city(callback.from_user.id)
    if city:
        await callback.message.edit_text(f"🏙 Ваш текущий город: {city}")
    else:
        await callback.message.edit_text("❌ Город не установлен. Нажмите «📍 Установить город».")
    await safe_answer(callback)

@router.callback_query(F.data == "weather_set")
async def weather_set_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "📍 Чтобы установить город, отправьте команду /setcity <название>, например:\n"
        "/setcity Москва"
    )
    await safe_answer(callback)

@router.callback_query(F.data == "weather_unset")
async def weather_unset_callback(callback: CallbackQuery):
    db.unsubscribe_user(callback.from_user.id)
    await callback.message.edit_text(
        "✅ Вы отписаны от утренней рассылки погоды. Чтобы подписаться снова, установите город."
    )
    await safe_answer(callback)

# Вспомогательная функция для безопасного ответа на callback
async def safe_answer(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass  # игнорируем ошибки устаревших callback