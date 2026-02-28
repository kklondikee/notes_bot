from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import io
import database as db
from processors.audio_processor import voice_to_text
from keyboards import main_menu, cancel_inline
from states import NoteStates

router = Router()

@router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext):
    print("DEBUG: handle_photo called")
    photo = message.photo[-1]
    file_id = photo.file_id
    await state.update_data(photo_file_id=file_id)
    await state.set_state(NoteStates.waiting_for_title)
    await message.answer(
        "Фото получено! Теперь отправьте заголовок для заметки\n"
        "(или отправьте '-' чтобы создать заметку без заголовка):",
        reply_markup=cancel_inline()
    )

@router.message(F.voice)
async def handle_voice(message: Message, state: FSMContext):
    print("DEBUG: handle_voice called")
    voice = message.voice
    file_id = voice.file_id
    status_msg = await message.answer("🎤 Распознаю речь... это может занять несколько секунд")

    try:
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        file_content = io.BytesIO()
        await message.bot.download_file(file_path, destination=file_content)
        file_content.seek(0)

        text = await voice_to_text(file_content.read())

        if not isinstance(text, str):
            text = ""

        if not text:
            await status_msg.edit_text("❌ Не удалось распознать речь. Попробуйте ещё раз или отправьте более чёткое сообщение.")
            return

        note_id = db.add_note(
            user_id=message.from_user.id,
            title="Голосовая заметка",
            text=text,
            remind_at=None
        )

        db.add_file(note_id, "voice", file_id)

        # Сначала редактируем статусное сообщение (без клавиатуры)
        await status_msg.edit_text(
            f"✅ Голосовая заметка сохранена!\n\n"
            f"📝 Текст: {text[:200]}{'...' if len(text) > 200 else ''}"
        )
        # Затем отправляем новое сообщение с главным меню
        await message.answer("Выберите действие:", reply_markup=main_menu())

    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка при обработке голоса: {e}")
        # Здесь тоже не нужно передавать клавиатуру

@router.message(F.document)
async def handle_document(message: Message, state: FSMContext):
    print("DEBUG: handle_document called")
    document = message.document
    file_id = document.file_id
    file_name = document.file_name
    await state.update_data(doc_file_id=file_id, doc_name=file_name)
    await state.set_state(NoteStates.waiting_for_title)
    await message.answer(
        f"Документ {file_name} получен! Теперь отправьте заголовок для заметки\n"
        "(или '-' чтобы пропустить):",
        reply_markup=cancel_inline()
    )