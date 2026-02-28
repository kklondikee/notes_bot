from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Новая заметка")],
            [KeyboardButton(text="📋 Мои заметки")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )

def notes_inline(notes):
    buttons = []
    for note_id, title in notes:
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"note_{note_id}")])
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

def tags_inline(tags):
    buttons = []
    for tag_name, count in tags:
        buttons.append([InlineKeyboardButton(text=f"{tag_name} ({count})", callback_data=f"tag_{tag_name}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)