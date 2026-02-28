from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime
import database as db
from keyboards import main_menu, notes_inline, note_actions_inline, confirm_delete_inline, cancel_inline
from states import NoteStates, EditNoteStates

router = Router()

# -------------------------------------------------------------------
# СОЗДАНИЕ НОВОЙ ЗАМЕТКИ
# -------------------------------------------------------------------
@router.message(Command("new"))
@router.message(F.text == "📝 Новая заметка")
async def new_note(message: Message, state: FSMContext):
    await state.set_state(NoteStates.waiting_for_title)
    await message.answer("Введите заголовок заметки:", reply_markup=cancel_inline())

@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Действие отменено.")
    await callback.answer()

@router.message(NoteStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(NoteStates.waiting_for_text)
    await message.answer("Теперь введите текст заметки:")

@router.message(NoteStates.waiting_for_text)
async def process_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(NoteStates.waiting_for_remind)
    await message.answer(
        "Хотите установить напоминание? Отправьте дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Или отправьте '-' чтобы пропустить."
    )

@router.message(NoteStates.waiting_for_remind)
async def process_remind(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data['title']
    text = data['text']
    remind_str = message.text.strip()
    remind_iso = None

    if remind_str != "-":
        try:
            dt = datetime.strptime(remind_str, "%d.%m.%Y %H:%M")
            remind_iso = dt.isoformat()
        except ValueError:
            await message.answer("Неверный формат. Попробуйте снова или отправьте '-'.")
            return

    note_id = db.add_note(message.from_user.id, title, text, remind_iso)
    await state.clear()
    await message.answer("✅ Заметка сохранена!", reply_markup=main_menu())

# -------------------------------------------------------------------
# ПРОСМОТР СПИСКА ЗАМЕТОК
# -------------------------------------------------------------------
@router.message(Command("list"))
@router.message(F.text == "📋 Мои заметки")
async def list_notes(message: Message):
    notes = db.get_user_notes(message.from_user.id)
    if not notes:
        await message.answer("У вас пока нет заметок.", reply_markup=main_menu())
        return
    kb = notes_inline(notes)
    await message.answer("Ваши заметки:", reply_markup=kb)

# -------------------------------------------------------------------
# ПРОСМОТР КОНКРЕТНОЙ ЗАМЕТКИ
# -------------------------------------------------------------------
@router.callback_query(F.data.startswith("note_"))
async def show_note(callback: CallbackQuery):
    note_id = int(callback.data.split("_")[1])
    note = db.get_note(note_id)
    if note:
        title, text, remind_at = note
        remind_str = f"\n\n⏰ Напоминание: {remind_at}" if remind_at else ""
        kb = note_actions_inline(note_id)
        await callback.message.answer(
            f"*{title}*\n\n{text}{remind_str}",
            parse_mode="Markdown",
            reply_markup=kb
        )
    else:
        await callback.message.answer("Заметка не найдена.")
    await callback.answer()

# -------------------------------------------------------------------
# УДАЛЕНИЕ ЗАМЕТКИ
# -------------------------------------------------------------------
@router.callback_query(F.data.startswith("delete_"))
async def delete_note_confirm(callback: CallbackQuery):
    note_id = int(callback.data.split("_")[1])
    kb = confirm_delete_inline(note_id)
    await callback.message.edit_text("Вы уверены, что хотите удалить эту заметку?", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_del_"))
async def delete_note(callback: CallbackQuery):
    note_id = int(callback.data.split("_")[2])
    db.delete_note(note_id)
    await callback.message.edit_text("🗑 Заметка удалена.")
    await callback.answer()

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

# -------------------------------------------------------------------
# РЕДАКТИРОВАНИЕ ЗАМЕТКИ (упрощённое: полностью заменяем содержимое)
# -------------------------------------------------------------------
@router.callback_query(F.data.startswith("edit_"))
async def edit_note_start(callback: CallbackQuery, state: FSMContext):
    note_id = int(callback.data.split("_")[1])
    note = db.get_note(note_id)
    if not note:
        await callback.message.answer("Заметка не найдена.")
        await callback.answer()
        return

    await state.update_data(edit_note_id=note_id, old_title=note[0], old_text=note[1], old_remind=note[2])
    await state.set_state(EditNoteStates.waiting_for_new_title)
    await callback.message.answer(
        f"Текущий заголовок: *{note[0]}*\nВведите новый заголовок (или отправьте '-' чтобы оставить прежний):",
        parse_mode="Markdown",
        reply_markup=cancel_inline()
    )
    await callback.answer()

@router.message(EditNoteStates.waiting_for_new_title)
async def edit_title(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text.strip() == "-":
        new_title = data['old_title']
    else:
        new_title = message.text.strip()
    await state.update_data(new_title=new_title)
    await state.set_state(EditNoteStates.waiting_for_new_text)
    await message.answer(f"Текущий текст: {data['old_text']}\nВведите новый текст (или '-' чтобы оставить прежний):")

@router.message(EditNoteStates.waiting_for_new_text)
async def edit_text(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text.strip() == "-":
        new_text = data['old_text']
    else:
        new_text = message.text.strip()
    await state.update_data(new_text=new_text)
    await state.set_state(EditNoteStates.waiting_for_new_remind)
    await message.answer(
        f"Текущее напоминание: {data['old_remind'] or 'не установлено'}\n"
        "Введите новую дату в формате ДД.ММ.ГГГГ ЧЧ:ММ (или '-' чтобы оставить, '0' чтобы удалить напоминание):"
    )

@router.message(EditNoteStates.waiting_for_new_remind)
async def edit_remind(message: Message, state: FSMContext):
    data = await state.get_data()
    remind_str = message.text.strip()
    new_remind = data['old_remind']

    if remind_str == "0":
        new_remind = None
    elif remind_str != "-":
        try:
            dt = datetime.strptime(remind_str, "%d.%m.%Y %H:%M")
            new_remind = dt.isoformat()
        except ValueError:
            await message.answer("Неверный формат. Попробуйте снова или отправьте '-'.")
            return

    db.update_note(
        note_id=data['edit_note_id'],
        title=data['new_title'],
        text=data['new_text'],
        remind_at=new_remind
    )
    await state.clear()
    await message.answer("✅ Заметка обновлена!", reply_markup=main_menu())