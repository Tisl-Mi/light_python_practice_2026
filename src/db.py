import sqlite3
import os

DB_PATH = "data/app.db"

def init_db(db_path=DB_PATH):
    """Создаёт папку data и файл базы, если их нет. Добавляет таблицу scan_sessions."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scan_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_path TEXT NOT NULL,
            scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print(f"База данных готова: {db_path}")

def insert_test_session(root_path):
    """Вставляет тестовую запись и возвращает её id."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO scan_sessions (root_path) VALUES (?)", (root_path,))
    conn.commit()
    session_id = cur.lastrowid
    conn.close()
    return session_id

def get_all_sessions():
    """Выводит все сессии из базы."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, root_path, scan_date FROM scan_sessions")
    rows = cur.fetchall()
    conn.close()
    return rows