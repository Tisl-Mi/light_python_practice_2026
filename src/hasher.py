"""
Хеширование файлов чанками (блоками) с использованием hashlib.
Размер чанка задаётся в байтах (по умолчанию 2 ГБ).
Такой подход позволяет обрабатывать файлы любого размера, не загружая их целиком в память.
"""

import hashlib

def compute_hash(file_path, chunk_size=2 * 1024 * 1024):
    """
    Вычисляет SHA-256 хеш файла.
    Аргументы:
        file_path  – абсолютный путь к файлу
        chunk_size – размер читаемого блока в байтах (по умолчанию 2 МБ)
    Возвращает:
        строку с шестнадцатеричным хешем или None при ошибке.
    """
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)   # читаем очередной блок
                if not chunk:                # конец файла
                    break
                sha256.update(chunk)         # обновляем хеш
    except (IOError, OSError):
        return None
    return sha256.hexdigest()