from aiogram.fsm.state import State, StatesGroup

class NoteStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_text = State()
    waiting_for_remind = State()

class EditNoteStates(StatesGroup):
    waiting_for_new_title = State()
    waiting_for_new_text = State()
    waiting_for_new_remind = State()