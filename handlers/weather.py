from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database as db
from weather import get_weather, get_weather_by_coords
from keyboards import main_menu, cancel_inline

router = Router()

class CitySelection(StatesGroup):
    waiting_for_choice = State()

@router.message(Command("setcity"))
async def set_city(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Введите название города после команды, например:\n/setcity Москва")
        return

    city = args[1].strip()
    status_msg = await message.answer("🔍 Ищу город...")

    weather_data, timezone, geo_options = await get_weather(city)

    if geo_options:
        buttons = []
        for opt in geo_options:
            buttons.append([InlineKeyboardButton(text=opt["name"], callback_data=f"cityopt_{opt['id']}")])
        await state.update_data(geo_options=geo_options, original_city=city)
        await state.set_state(CitySelection.waiting_for_choice)
        await status_msg.edit_text(
            "Найдено несколько городов. Уточните, какой вы имели в виду:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        return

    if not weather_data:
        await status_msg.edit_text("❌ Город не найден. Проверьте название и попробуйте снова.")
        return

    db.set_user_city(message.from_user.id, weather_data["city"], timezone)
    await status_msg.edit_text(
        f"✅ Город {weather_data['city']} сохранён! Часовой пояс: {timezone}\n"
        f"Теперь вы будете получать погоду каждое утро в 7:00 по местному времени.\n\n"
        f"Текущая погода:\n{weather_data['icon']} {weather_data['description']}\n"
        f"🌡 {weather_data['temperature']}°C, ветер {weather_data['wind_speed']} м/с"
    )

@router.callback_query(CitySelection.waiting_for_choice, F.data.startswith("cityopt_"))
async def city_chosen(callback: CallbackQuery, state: FSMContext):
    opt_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    geo_options = data.get("geo_options", [])
    if opt_id >= len(geo_options):
        await callback.message.edit_text("Ошибка выбора. Попробуйте снова.")
        await state.clear()
        return

    chosen = geo_options[opt_id]
    lat, lon = chosen["lat"], chosen["lon"]
    city_name = chosen["full_name"]

    weather_data, timezone = await get_weather_by_coords(lat, lon, city_name)

    if not weather_data:
        await callback.message.edit_text("❌ Не удалось получить погоду для выбранного города.")
        await state.clear()
        return

    db.set_user_city(callback.from_user.id, weather_data["city"], timezone)
    await callback.message.edit_text(
        f"✅ Город {weather_data['city']} сохранён! Часовой пояс: {timezone}\n"
        f"Теперь вы будете получать погоду каждое утро в 7:00 по местному времени.\n\n"
        f"Текущая погода:\n{weather_data['icon']} {weather_data['description']}\n"
        f"🌡 {weather_data['temperature']}°C, ветер {weather_data['wind_speed']} м/с"
    )
    await state.clear()
    await callback.answer()

@router.message(Command("mycity"))
async def my_city(message: Message):
    city, tz = db.get_user_city(message.from_user.id)
    if city:
        await message.answer(f"🏙 Ваш текущий город: {city}\n🕐 Часовой пояс: {tz}")
    else:
        await message.answer("❌ Город не установлен. Используйте /setcity для настройки.")

@router.message(Command("weather"))
async def weather_now(message: Message):
    city, tz = db.get_user_city(message.from_user.id)
    if not city:
        await message.answer("❌ Сначала установите город через /setcity")
        return

    status_msg = await message.answer("🌤 Получаю данные о погоде...")
    weather_data, _, _ = await get_weather(city)  # timezone не нужен здесь

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