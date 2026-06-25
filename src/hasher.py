import hashlib

def compute_hash(file_path, chunk_size=2 * 1024 * 1024 * 1024):
    """
    Вычисляет SHA-256 хеш файла, читая его чанками заданного размера.
    Возвращает шестнадцатеричную строку хеша или None при ошибке.
    """
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                sha256.update(chunk)
    except (IOError, OSError):
        return None
    return sha256.hexdigest()