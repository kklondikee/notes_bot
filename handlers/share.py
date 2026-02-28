from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import database as db
import sqlite3
from keyboards import notes_inline, main_menu

router = Router()

async def get_user_id_by_username(bot, username: str) -> int | None:
    """
    Пытается получить user_id по username через Telegram API.
    Возвращает ID или None, если пользователь не найден (никогда не взаимодействовал с ботом).
    """
    try:
        # Убираем @, если есть
        clean_username = username.lstrip('@')
        chat = await bot.get_chat(f"@{clean_username}")
        return chat.id
    except Exception:
        return None

@router.message(Command("share"))
async def share_note_command(message: Message):
    """
    Формат: /share <note_id> <@username или ID>
    Пример: /share 5 @durov
    """
    args = message.text.split()
    if len(args) != 3:
        await message.answer(
            "❌ Неправильный формат. Используйте:\n"
            "/share <id заметки> <@username или числовой ID>\n"
            "Пример: /share 5 @durov"
        )
        return

    note_id_str = args[1]
    target_identifier = args[2].strip()

    # Проверяем, что note_id — число
    try:
        note_id = int(note_id_str)
    except ValueError:
        await message.answer("❌ ID заметки должен быть числом.")
        return

    # Определяем, передан ли username (начинается с @) или числовой ID
    if target_identifier.startswith('@'):
        # Пытаемся получить user_id по username
        target_user_id = await get_user_id_by_username(message.bot, target_identifier)
        if target_user_id is None:
            await message.answer(
                f"❌ Пользователь {target_identifier} не найден.\n"
                f"Убедитесь, что username правильный, и что этот пользователь когда-либо писал боту (или есть в общих группах).\n"
                f"Если не получается, попросите пользователя узнать свой числовой ID через @userinfobot и введите его вместо username."
            )
            return
    else:
        # Пробуем как числовой ID
        try:
            target_user_id = int(target_identifier)
        except ValueError:
            await message.answer("❌ Целевой идентификатор должен быть @username или числовым ID.")
            return

    # Проверяем, что заметка существует и пользователь — владелец
    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id, title FROM notes WHERE id = ?", (note_id,))
    note_row = cur.fetchone()
    conn.close()

    if not note_row:
        await message.answer("❌ Заметка с таким ID не найдена.")
        return

    owner_id, note_title = note_row
    if owner_id != message.from_user.id:
        await message.answer("❌ Вы не являетесь владельцем этой заметки.")
        return

    # Проверяем, что целевой пользователь вообще существует (хотя бы есть в таблице notes)
    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM notes WHERE user_id = ? LIMIT 1", (target_user_id,))
    target_exists = cur.fetchone()
    conn.close()

    if not target_exists:
        await message.answer(
            "❌ Пользователь с таким ID никогда не создавал заметок.\n"
            "Возможно, он ещё не пользовался ботом. Попросите его написать боту хотя бы /start."
        )
        return

    # Предоставляем доступ
    db.share_note(note_id, message.from_user.id, target_user_id)
    await message.answer(f"✅ Заметка «{note_title}» открыта для пользователя {target_identifier}.")

    # Уведомляем целевого пользователя
    try:
        await message.bot.send_message(
            target_user_id,
            f"🔔 Пользователь {message.from_user.full_name} (ID: {message.from_user.id}) открыл вам доступ к заметке «{note_title}».\n"
            f"Посмотреть: /shared"
        )
    except Exception:
        # Если не можем отправить сообщение (пользователь не начинал диалог с ботом) – игнорируем
        pass

@router.message(Command("shared"))
async def list_shared_notes(message: Message):
    notes = db.get_shared_notes(message.from_user.id)
    if not notes:
        await message.answer("У вас нет общих заметок.")
        return
    simple_notes = [(nid, title) for nid, title, owner_id in notes]
    kb = notes_inline(simple_notes, prefix="shared_note")
    await message.answer("📂 Заметки, доступные вам:", reply_markup=kb)

@router.callback_query(F.data.startswith("shared_note_"))
async def show_shared_note(callback: CallbackQuery):
    note_id = int(callback.data.split("_")[2])
    result = db.get_shared_note(note_id, callback.from_user.id)
    if not result:
        await callback.message.answer("❌ Заметка не найдена или доступ запрещён.")
        await callback.answer()
        return

    if len(result) == 4:
        title, text, remind_at, is_owner = result
        owner_info = ""
    else:
        title, text, remind_at, owner_id, is_owner = result
        owner_info = f"\n👤 Автор: `{owner_id}`"

    remind_str = f"\n\n⏰ Напоминание: {remind_at}" if remind_at else ""
    tags = db.get_note_tags(note_id)
    tags_str = f"\n\n🏷 Теги: {', '.join(tags)}" if tags else ""
    files = db.get_note_files(note_id)

    # Добавляем ID в начало сообщения
    header = f"*{title}*\n🆔 ID: `{note_id}`{owner_info}"
    await callback.message.answer(
        f"{header}\n\n{text}{remind_str}{tags_str}",
        parse_mode="Markdown"
    )
    for file_type, file_id in files:
        if file_type == 'photo':
            await callback.message.answer_photo(photo=file_id)
        elif file_type == 'voice':
            await callback.message.answer_voice(voice=file_id)
        elif file_type == 'document':
            await callback.message.answer_document(document=file_id)
    await callback.answer()

# Дополнительная команда для получения ID по username (полезно для админов)
@router.message(Command("resolve"))
async def resolve_username(message: Message):
    """Получить ID пользователя по @username (если он доступен боту)."""
    args = message.text.split()
    if len(args) != 2:
        await message.answer("Использование: /resolve @username")
        return
    username = args[1]
    user_id = await get_user_id_by_username(message.bot, username)
    if user_id:
        await message.answer(f"🆔 Пользователь {username} имеет ID: `{user_id}`", parse_mode="Markdown")
    else:
        await message.answer(f"❌ Не удалось найти пользователя {username}. Убедитесь, что он писал боту.")