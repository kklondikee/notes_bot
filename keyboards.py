from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    """Главная reply-клавиатура."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Новая заметка")],
            [KeyboardButton(text="📋 Мои заметки")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )

def notes_inline(notes):
    """Инлайн-клавиатура со списком заметок (заголовки)."""
    buttons = []
    for note_id, title in notes:
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"note_{note_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def note_actions_inline(note_id: int):
    """Инлайн-кнопки для конкретной заметки (редактировать/удалить)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{note_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{note_id}")
        ]
    ])

def confirm_delete_inline(note_id: int):
    """Подтверждение удаления."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_del_{note_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="cancel_delete")
        ]
    ])

def cancel_inline():
    """Кнопка отмены действия."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])