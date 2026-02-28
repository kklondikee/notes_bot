from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
import database as db                          # добавили импорт БД
from keyboards import main_menu, weather_inline # добавили weather_inline

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот для заметок 📝\n\n"
        "Ты можешь создавать заметки и устанавливать напоминания.\n"
        "Используй кнопки ниже или команды /new, /list, /help, /search, /tags.",
        reply_markup=main_menu()
    )

@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    await message.answer(
        "Команды:\n"
        "/start - приветствие\n"
        "/new - создать заметку\n"
        "/list - мои заметки\n"
        "/search слово - поиск по заметкам\n"
        "/tags - все теги\n"
        "/help - помощь\n\n"
        "Также можно отправлять фото и голосовые сообщения."
    )

# НОВЫЙ ОБРАБОТЧИК ДЛЯ КНОПКИ "🌤 Погода"
@router.message(F.text == "🌤 Погода")
async def weather_menu(message: Message):
    """Показывает инлайн-меню с действиями для погоды."""
    city = db.get_user_city(message.from_user.id)
    has_city = city is not None
    kb = weather_inline(has_city)
    await message.answer("🌤 Выберите действие:", reply_markup=kb)