from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
import database as db
from keyboards import main_menu, weather_inline

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "🌟 *Добро пожаловать в Notes Bot!* 🌟\n\n"
        "Я помогу вам сохранять важные мысли, ставить напоминания и не забывать о делах.\n\n"
        "📝 *Основные возможности:*\n"
        "• Создание заметок с заголовком и текстом\n"
        "• Установка напоминаний на нужное время\n"
        "• Добавление тегов для удобной сортировки\n"
        "• Поиск по заметкам\n"
        "• Голосовой ввод (просто отправьте голосовое сообщение)\n"
        "• Прикрепление фото к заметкам\n"
        "• Ежедневный прогноз погоды в 7 утра (по желанию)\n\n"
        "🛠 *Команды:*\n"
        "/new – создать заметку\n"
        "/list – показать все заметки\n"
        "/search <слово> – поиск\n"
        "/tags – список ваших тегов\n"
        "/tag <тег> – заметки с тегом\n"
        "/setcity <город> – настроить погоду\n"
        "/weather – погода сейчас\n"
        "/menu – главное меню\n"
        "/help – подробная помощь\n\n"
        "Используйте кнопки ниже для быстрого доступа 👇"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_menu())

@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    help_text = (
        "📘 *Справка по командам Notes Bot*\n\n"
        "📝 *Заметки:*\n"
        "/new – создать новую заметку (бот проведёт по шагам)\n"
        "/list – список всех ваших заметок\n"
        "/search <слово> – найти заметки по тексту или заголовку\n"
        "/tags – показать все ваши теги и количество заметок\n"
        "/tag <тег> – показать заметки с определённым тегом\n\n"
        "⏰ *Напоминания:*\n"
        "При создании заметки можно указать дату и время в формате `ДД.ММ.ГГГГ ЧЧ:ММ`\n"
        "Бот пришлёт уведомление в указанное время\n\n"
        "🎤 *Голос и фото:*\n"
        "• Отправьте голосовое сообщение – бот распознает речь и создаст заметку\n"
        "• Отправьте фото – бот предложит добавить заголовок и текст, сохранит фото\n\n"
        "🌤 *Погода:*\n"
        "/setcity <город> – установить ваш город для ежедневной рассылки в 7:00\n"
        "/weather – узнать погоду сейчас\n"
        "/mycity – показать текущий город и часовой пояс\n"
        "/unsetcity – отписаться от утренней рассылки\n\n"
        "❓ *Другое:*\n"
        "/menu – показать главное меню\n"
        "/help – показать это сообщение\n\n"
        "Если у вас есть вопросы или предложения, пишите @администратор"
    )
    await message.answer(help_text, parse_mode="Markdown", reply_markup=main_menu())

@router.message(Command("menu"))
@router.message(F.text == "📱 Меню")
async def show_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu())

@router.message(F.text == "🌤 Погода")
async def weather_menu(message: Message):
    city, tz = db.get_user_city(message.from_user.id)
    has_city = city is not None
    kb = weather_inline(has_city)
    await message.answer("🌤 Выберите действие:", reply_markup=kb)