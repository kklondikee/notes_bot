import sqlite3
from datetime import datetime

DB_NAME = "notes.db"

def init_db():
    """Создаёт таблицы, если их нет."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                remind_at TEXT,
                sent INTEGER DEFAULT 0
            )
        """)
        conn.commit()

def add_note(user_id: int, title: str, text: str, remind_at: str = None) -> int:
    """Добавляет заметку, возвращает её ID."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO notes (user_id, title, text, remind_at) VALUES (?, ?, ?, ?)",
            (user_id, title, text, remind_at)
        )
        conn.commit()
        return cur.lastrowid

def get_user_notes(user_id: int):
    """Возвращает список (id, title) для пользователя."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title FROM notes WHERE user_id = ? ORDER BY id DESC",
            (user_id,)
        )
        return cur.fetchall()

def get_note(note_id: int):
    """Возвращает (title, text, remind_at) для заметки или None."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT title, text, remind_at FROM notes WHERE id = ?",
            (note_id,)
        )
        row = cur.fetchone()
        return row if row else None

def update_note(note_id: int, title: str = None, text: str = None, remind_at: str = None):
    """Обновляет поля заметки. Если параметр None – не меняется."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        if title is not None:
            cur.execute("UPDATE notes SET title = ? WHERE id = ?", (title, note_id))
        if text is not None:
            cur.execute("UPDATE notes SET text = ? WHERE id = ?", (text, note_id))
        if remind_at is not None:
            cur.execute("UPDATE notes SET remind_at = ?, sent = 0 WHERE id = ?", (remind_at, note_id))
        conn.commit()

def delete_note(note_id: int):
    """Удаляет заметку."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()

def get_pending_reminders():
    """Возвращает список (id, user_id, title, text) для напоминаний, которые нужно отправить."""
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, user_id, title, text FROM notes WHERE remind_at <= ? AND sent = 0",
            (now,)
        )
        return cur.fetchall()

def mark_reminder_sent(note_id: int):
    """Отмечает напоминание как отправленное."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE notes SET sent = 1 WHERE id = ?", (note_id,))
        conn.commit()