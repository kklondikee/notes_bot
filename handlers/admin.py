from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database as db
from config import ADMIN_IDS

router = Router()

# Класс состояний для рассылки
class BroadcastStates(StatesGroup):
    waiting_for_text = State()

# Проверка на администратора
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# Декоратор для команд, доступных только админам
def admin_only(func):
    async def wrapper(message: Message, *args, **kwargs):
        if is_admin(message.from_user.id):
            return await func(message, *args, **kwargs)
        else:
            await message.answer("⛔ Доступ запрещён. Эта команда только для администраторов.")
    return wrapper

# Вспомогательная функция для получения user_id по username
async def get_user_id_by_username(bot, username: str) -> int | None:
    try:
        clean_username = username.lstrip('@')
        chat = await bot.get_chat(f"@{clean_username}")
        return chat.id
    except Exception:
        return None

# ------------------------------------------------------------
# Главное меню админки (инлайн-кнопки)
# ------------------------------------------------------------
def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="👥 Пользователи", callback_data="admin_users")
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.button(text="📨 Отправить сообщение", callback_data="admin_say")
    builder.adjust(2)
    return builder.as_markup()

@router.message(Command("admin"))
@admin_only
async def admin_menu(message: Message, **kwargs):
    await message.answer(
        "🔐 *Панель администратора*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard()
    )

# ------------------------------------------------------------
# Статистика
# ------------------------------------------------------------
def get_stats():
    import sqlite3
    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT user_id) FROM notes")
    users_with_notes = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT user_id) FROM users")
    users_with_settings = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM notes")
    total_notes = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM notes WHERE remind_at IS NOT NULL")
    notes_with_reminders = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE city IS NOT NULL AND subscribed = 1")
    weather_subscribers = cur.fetchone()[0]
    conn.close()
    return {
        "users_with_notes": users_with_notes,
        "users_with_settings": users_with_settings,
        "total_notes": total_notes,
        "notes_with_reminders": notes_with_reminders,
        "weather_subscribers": weather_subscribers,
    }

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    stats = get_stats()
    text = (
        "📊 *Статистика*\n\n"
        f"👥 Пользователей с заметками: {stats['users_with_notes']}\n"
        f"⚙️ Пользователей с настройками: {stats['users_with_settings']}\n"
        f"📝 Всего заметок: {stats['total_notes']}\n"
        f"⏰ С напоминаниями: {stats['notes_with_reminders']}\n"
        f"🌤 Подписок на погоду: {stats['weather_subscribers']}"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=admin_keyboard())
    await callback.answer()

# ------------------------------------------------------------
# Список пользователей
# ------------------------------------------------------------
def get_all_users():
    import sqlite3
    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id, COUNT(*) as notes_count FROM notes GROUP BY user_id")
    notes_counts = dict(cur.fetchall())
    cur.execute("SELECT user_id, city, subscribed FROM users")
    users_data = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
    conn.close()
    all_ids = set(notes_counts.keys()) | set(users_data.keys())
    result = []
    for uid in sorted(all_ids):
        notes_count = notes_counts.get(uid, 0)
        city, subscribed = users_data.get(uid, (None, 0))
        result.append((uid, notes_count, city, subscribed))
    return result

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    users = get_all_users()
    if not users:
        await callback.message.edit_text("❌ Пользователей нет.", reply_markup=admin_keyboard())
        await callback.answer()
        return
    text = "👥 *Список пользователей*\n\n"
    for user_id, notes_count, city, subscribed in users:
        city_str = f", город: {city}" if city else ""
        sub_str = "✅" if subscribed else "❌" if city else ""
        text += f"• `{user_id}`: {notes_count} зам.{city_str} {sub_str}\n"
    if len(text) > 4096:
        text = text[:4000] + "\n\n... (обрезано)"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=admin_keyboard())
    await callback.answer()

# ------------------------------------------------------------
# Рассылка сообщений всем пользователям
# ------------------------------------------------------------
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📢 Введите текст для рассылки всем пользователям.\n"
        "Отправьте его в ответ на это сообщение.\n"
        "Для отмены отправьте /cancel"
    )
    await state.set_state(BroadcastStates.waiting_for_text)
    await callback.answer()

@router.message(BroadcastStates.waiting_for_text)
async def admin_broadcast_send(message: Message, state: FSMContext):
    text = message.text
    if text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Рассылка отменена.")
        return
    import sqlite3
    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT user_id FROM notes")
    users = [row[0] for row in cur.fetchall()]
    conn.close()
    if not users:
        await message.answer("❌ Нет пользователей для рассылки.")
        await state.clear()
        return
    await message.answer(f"⏳ Начинаю рассылку для {len(users)} пользователей...")
    success = 0
    failed = 0
    for user_id in users:
        try:
            await message.bot.send_message(
                user_id,
                f"📢 *Сообщение от администратора*\n\n{text}",
                parse_mode="Markdown"
            )
            success += 1
        except Exception as e:
            failed += 1
            print(f"Ошибка отправки пользователю {user_id}: {e}")
    await message.answer(f"✅ Рассылка завершена.\nУспешно: {success}\nОшибок: {failed}")
    await state.clear()

# ------------------------------------------------------------
# Отправка сообщения конкретному пользователю (с поддержкой username)
# ------------------------------------------------------------
@router.callback_query(F.data == "admin_say")
async def admin_say_start(callback: CallbackQuery):
    await callback.message.edit_text(
        "📨 Введите команду в формате:\n`/say <user_id или @username> <текст>`\n"
        "Например: `/say @durov Привет!` или `/say 123456789 Привет!`"
    )
    await callback.answer()

@router.message(Command("say"))
@admin_only
async def admin_say(message: Message, **kwargs):   # добавили **kwargs
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("❌ Неправильный формат. Используйте: `/say <user_id или @username> <текст>`")
        return
    target_identifier = parts[1].strip()
    text = parts[2]

    # Определяем, является ли идентификатор username (начинается с @)
    if target_identifier.startswith('@'):
        target_user_id = await get_user_id_by_username(message.bot, target_identifier)
        if target_user_id is None:
            await message.answer(f"❌ Пользователь {target_identifier} не найден. Убедитесь, что он писал боту.")
            return
    else:
        try:
            target_user_id = int(target_identifier)
        except ValueError:
            await message.answer("❌ Идентификатор должен быть числовым ID или @username.")
            return

    try:
        await message.bot.send_message(
            target_user_id,
            f"📨 *Сообщение от администратора*\n\n{text}",
            parse_mode="Markdown"
        )
        await message.answer(f"✅ Сообщение отправлено пользователю {target_identifier}.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ------------------------------------------------------------
# Команда для получения ID по username (полезна админу)
# ------------------------------------------------------------
@router.message(Command("resolve"))
@admin_only
async def resolve_username(message: Message, **kwargs):   # добавили **kwargs
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

# ------------------------------------------------------------
# Возврат в админ-меню
# ------------------------------------------------------------
@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔐 *Панель администратора*\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard()
    )
    await callback.answer()