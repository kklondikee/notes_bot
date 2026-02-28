import sqlite3
from datetime import datetime

DB_NAME = "notes.db"

# ==================== ОСНОВНЫЕ ТАБЛИЦЫ ====================

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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER NOT NULL,
                file_type TEXT NOT NULL,
                file_id TEXT NOT NULL,
                FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    init_tags_tables()

def add_note(user_id: int, title: str, text: str, remind_at: str = None) -> int:
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO notes (user_id, title, text, remind_at) VALUES (?, ?, ?, ?)",
            (user_id, title, text, remind_at)
        )
        conn.commit()
        return cur.lastrowid

def get_user_notes(user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title FROM notes WHERE user_id = ? ORDER BY id DESC",
            (user_id,)
        )
        return cur.fetchall()

def get_note(note_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT title, text, remind_at FROM notes WHERE id = ?",
            (note_id,)
        )
        row = cur.fetchone()
        return row if row else None

def update_note(note_id: int, title: str = None, text: str = None, remind_at: str = None):
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
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()

def get_pending_reminders():
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, user_id, title, text FROM notes WHERE remind_at <= ? AND sent = 0",
            (now,)
        )
        return cur.fetchall()

def mark_reminder_sent(note_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE notes SET sent = 1 WHERE id = ?", (note_id,))
        conn.commit()

# ==================== РАБОТА С ФАЙЛАМИ ====================

def add_file(note_id: int, file_type: str, file_id: str):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO files (note_id, file_type, file_id) VALUES (?, ?, ?)",
            (note_id, file_type, file_id)
        )
        conn.commit()

def get_note_files(note_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT file_type, file_id FROM files WHERE note_id = ?",
            (note_id,)
        )
        return cur.fetchall()

def delete_note_files(note_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM files WHERE note_id = ?", (note_id,))
        conn.commit()

# ==================== ПОИСК ====================

def search_notes(user_id: int, query: str):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        like_query = f"%{query}%"
        cur.execute("""
            SELECT id, title FROM notes
            WHERE user_id = ? AND (title LIKE ? OR text LIKE ?)
            ORDER BY id DESC
        """, (user_id, like_query, like_query))
        return cur.fetchall()

# ==================== ТЕГИ ====================

def init_tags_tables():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                UNIQUE(name, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS note_tags (
                note_id INTEGER,
                tag_id INTEGER,
                FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (note_id, tag_id)
            )
        """)
        conn.commit()

def add_tag(user_id: int, tag_name: str) -> int:
    tag_name = tag_name.strip().lower()
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO tags (name, user_id) VALUES (?, ?)",
                (tag_name, user_id)
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            cur.execute(
                "SELECT id FROM tags WHERE name = ? AND user_id = ?",
                (tag_name, user_id)
            )
            return cur.fetchone()[0]

def add_note_tags(note_id: int, tag_ids: list):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        for tag_id in tag_ids:
            cur.execute(
                "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
                (note_id, tag_id)
            )
        conn.commit()

def get_note_tags(note_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.name FROM tags t
            JOIN note_tags nt ON t.id = nt.tag_id
            WHERE nt.note_id = ?
        """, (note_id,))
        return [row[0] for row in cur.fetchall()]

def get_user_tags(user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.name, COUNT(nt.note_id) as cnt
            FROM tags t
            LEFT JOIN note_tags nt ON t.id = nt.tag_id
            WHERE t.user_id = ?
            GROUP BY t.id
            ORDER BY t.name
        """, (user_id,))
        return cur.fetchall()

def update_note_tags(note_id: int, new_tag_ids: list):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
        for tag_id in new_tag_ids:
            cur.execute(
                "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
                (note_id, tag_id)
            )
        conn.commit()