import sqlite3
from datetime import datetime

DB_NAME = "notes.db"

# ==================== ОСНОВНЫЕ ТАБЛИЦЫ ====================

def init_db():
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
    init_users_table()
    init_shared_table()   # <-- добавить эту строку

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

# ==================== ПОЛЬЗОВАТЕЛИ И ГОРОДА ====================

def init_users_table():
    """Создаёт таблицу users, если её нет."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                city TEXT,
                subscribed INTEGER DEFAULT 1
            )
        """)
        conn.commit()

def set_user_city(user_id: int, city: str):
    """Сохраняет город пользователя."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, city) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET city = ?
        """, (user_id, city, city))
        conn.commit()

def get_user_city(user_id: int) -> str | None:
    """Возвращает сохранённый город пользователя или None."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT city FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else None

def unsubscribe_user(user_id: int):
    """Отписывает пользователя от рассылки."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, city, subscribed) VALUES (?, NULL, 0)
            ON CONFLICT(user_id) DO UPDATE SET city = NULL, subscribed = 0
        """, (user_id,))
        conn.commit()

def get_subscribed_users():
    """Возвращает список (user_id, city) всех подписанных пользователей."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, city FROM users WHERE city IS NOT NULL AND subscribed = 1")
        return cur.fetchall()

# ==================== ПОЛЬЗОВАТЕЛИ И ГОРОДА ====================

def init_users_table():
    """Создаёт таблицу users, если её нет."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                city TEXT,
                subscribed INTEGER DEFAULT 1
            )
        """)
        conn.commit()

def set_user_city(user_id: int, city: str):
    """Сохраняет город пользователя."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, city) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET city = ?
        """, (user_id, city, city))
        conn.commit()

def get_user_city(user_id: int) -> str | None:
    """Возвращает сохранённый город пользователя или None."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT city FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else None

def unsubscribe_user(user_id: int):
    """Отписывает пользователя от рассылки."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, city, subscribed) VALUES (?, NULL, 0)
            ON CONFLICT(user_id) DO UPDATE SET city = NULL, subscribed = 0
        """, (user_id,))
        conn.commit()

def get_subscribed_users():
    """Возвращает список (user_id, city) всех подписанных пользователей."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, city FROM users WHERE city IS NOT NULL AND subscribed = 1")
        return cur.fetchall()

# ==================== СОВМЕСТНЫЕ ЗАМЕТКИ ====================

def init_shared_table():
    """Создаёт таблицу для совместных заметок."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS shared_notes (
                note_id INTEGER,
                shared_with_user_id INTEGER,
                owner_user_id INTEGER,
                PRIMARY KEY (note_id, shared_with_user_id),
                FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
            )
        """)
        conn.commit()

# Добавьте вызов init_shared_table() в функцию init_db() после создания других таблиц.

def share_note(note_id: int, owner_id: int, target_user_id: int):
    """Предоставляет доступ к заметке другому пользователю."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO shared_notes (note_id, shared_with_user_id, owner_user_id) VALUES (?, ?, ?)",
            (note_id, target_user_id, owner_id)
        )
        conn.commit()

def get_shared_notes(user_id: int):
    """Возвращает список заметок, доступных пользователю (чужие, расшаренные с ним)."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT n.id, n.title, n.user_id as owner_id
            FROM notes n
            JOIN shared_notes s ON n.id = s.note_id
            WHERE s.shared_with_user_id = ?
            ORDER BY n.id DESC
        """, (user_id,))
        return cur.fetchall()  # список (id, title, owner_id)

def get_shared_note(note_id: int, user_id: int):
    """Возвращает заметку, если пользователь имеет к ней доступ (владелец или есть в shared)."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        # Проверяем, является ли пользователь владельцем
        cur.execute("SELECT user_id FROM notes WHERE id = ?", (note_id,))
        row = cur.fetchone()
        if row and row[0] == user_id:
            # владелец – полный доступ
            cur.execute("SELECT title, text, remind_at FROM notes WHERE id = ?", (note_id,))
            return cur.fetchone() + (True,)  # (title, text, remind_at, is_owner)
        # Иначе проверяем shared
        cur.execute("""
            SELECT n.title, n.text, n.remind_at, n.user_id
            FROM notes n
            JOIN shared_notes s ON n.id = s.note_id
            WHERE n.id = ? AND s.shared_with_user_id = ?
        """, (note_id, user_id))
        row = cur.fetchone()
        if row:
            return row + (False,)  # (title, text, remind_at, owner_id, is_owner=False)
        return None