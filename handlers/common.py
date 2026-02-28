from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from keyboards import main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот для заметок 📝\n\n"
        "Ты можешь создавать заметки и устанавливать напоминания.\n"
        "Используй кнопки ниже или команды /new, /list, /help.",
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
        "/help - помощь\n\n"
        "Или используй кнопки меню."
    )