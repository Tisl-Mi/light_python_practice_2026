"""
Взаимодействие с базой данных SQLite.
Использует только модуль sqlite3 (стандартная библиотека).
Таблицы:
  - scan_sessions   : сессии сканирования (дата, корневая папка)
  - files           : информация о каждом файле (путь, размер, хеш и т.д.)
  - backup_reports  : отчёты сравнения с резервной копией
"""

import sqlite3
import os
import json

DB_PATH = "data/app.db"   # файл базы данных

def init_db(db_path=DB_PATH):
    """
    Создаёт папку data (если нужно) и файл базы данных.
    Выполняет CREATE TABLE IF NOT EXISTS для всех таблиц.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS scan_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_path TEXT NOT NULL,
            scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            relative_path TEXT NOT NULL,
            filename TEXT NOT NULL,
            extension TEXT,
            size_bytes INTEGER,
            modified_time REAL,
            content_hash TEXT,
            FOREIGN KEY (session_id) REFERENCES scan_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS backup_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path TEXT NOT NULL,
            backup_path TEXT NOT NULL,
            report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            missing_count INTEGER DEFAULT 0,
            changed_count INTEGER DEFAULT 0,
            extra_count INTEGER DEFAULT 0,
            details TEXT
        );
    """)
    conn.commit()
    conn.close()
    print(f"База данных готова: {db_path}")

def create_session(root_path):
    """
    Создаёт новую запись в scan_sessions.
    Возвращает id созданной сессии.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO scan_sessions (root_path) VALUES (?)", (root_path,))
    conn.commit()
    session_id = cur.lastrowid
    conn.close()
    return session_id

def save_files(session_id, files):
    """
    Сохраняет список словарей (результат scan_directory) в таблицу files.
    files – список словарей с ключами:
        rel_path, filename, extension, size_bytes, modified
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for f in files:
        cur.execute("""
            INSERT INTO files
                (session_id, relative_path, filename, extension, size_bytes, modified_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            f['rel_path'],
            f['filename'],
            f['extension'],
            f['size_bytes'],
            f['modified']
        ))
    conn.commit()
    conn.close()

def get_files_by_session(session_id):
    """
    Возвращает все записи из таблицы files для указанной сессии.
    Каждая запись – кортеж:
        (id, relative_path, filename, extension, size_bytes, modified_time, content_hash)
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, relative_path, filename, extension, size_bytes, modified_time, content_hash
        FROM files
        WHERE session_id = ?
    """, (session_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def update_hash(file_id, hash_value):
    """
    Обновляет поле content_hash для конкретного файла (по его id).
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE files SET content_hash = ? WHERE id = ?", (hash_value, file_id))
    conn.commit()
    conn.close()

def find_duplicates(session_id):
    """
    Ищет дубликаты внутри сессии: группирует файлы с одинаковым хешем,
    оставляя только те хеши, которые встречаются > 1 раза.
    Возвращает список кортежей: (hash, [список относительных путей]).
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT content_hash, GROUP_CONCAT(relative_path, '|')
        FROM files
        WHERE session_id = ? AND content_hash IS NOT NULL
        GROUP BY content_hash
        HAVING COUNT(*) > 1
    """, (session_id,))
    rows = cur.fetchall()
    conn.close()

    result = []
    for hash_val, paths_concat in rows:
        paths = paths_concat.split('|')
        result.append((hash_val, paths))
    return result

def save_backup_report(source_path, backup_path, missing, changed, extra):
    """
    Сохраняет отчёт сравнения с бэкапом.
    missing, changed, extra – списки относительных путей.
    """
    details = json.dumps({
        "missing": missing,
        "changed": changed,
        "extra": extra
    }, ensure_ascii=False, indent=2)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO backup_reports
            (source_path, backup_path, missing_count, changed_count, extra_count, details)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (source_path, backup_path, len(missing), len(changed), len(extra), details))
    conn.commit()
    conn.close()