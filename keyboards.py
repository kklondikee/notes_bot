from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Новая заметка")],
            [KeyboardButton(text="📋 Мои заметки")],
            [KeyboardButton(text="🌤 Погода")],
            [KeyboardButton(text="📱 Меню")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )

def notes_inline(notes, prefix="note"):
    buttons = []
    for note_id, title in notes:
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"{prefix}_{note_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def note_actions_inline(note_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{note_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{note_id}")
        ]
    ])

def confirm_delete_inline(note_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_del_{note_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="cancel_delete")
        ]
    ])

def cancel_inline():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])

def weather_inline(has_city: bool = False):
    buttons = []
    buttons.append([InlineKeyboardButton(text="🌍 Погода сейчас", callback_data="weather_now")])
    buttons.append([InlineKeyboardButton(text="🏙 Мой город", callback_data="weather_mycity")])
    buttons.append([InlineKeyboardButton(text="📍 Установить город", callback_data="weather_set")])
    if has_city:
        buttons.append([InlineKeyboardButton(text="🚫 Отписаться от рассылки", callback_data="weather_unset")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)