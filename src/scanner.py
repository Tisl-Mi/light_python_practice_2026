import os

def scan_directory(directory, root_directory=None, verbose=False, _depth=0):
    """
    Рекурсивно обходит directory и возвращает список словарей.
    root_directory – исходная папка, относительно которой считаются относительные пути.
    Если не задан, считается равным directory (только при первом вызове).
    """
    if root_directory is None:
        root_directory = directory

    result = []
    try:
        entries = os.listdir(directory)
    except PermissionError:
        if verbose:
            print("  " * _depth + f"[ЗАКРЫТ] {directory}")
        return result

    if verbose:
        print("  " * _depth + f"[ПАПКА] {directory}")

    for entry in entries:
        full = os.path.join(directory, entry)
        if os.path.isdir(full):
            result.extend(scan_directory(full, root_directory, verbose, _depth + 1))
        else:
            try:
                stat = os.stat(full)
                size = stat.st_size
                mtime = stat.st_mtime
            except OSError:
                size = 0
                mtime = 0

            _, ext = os.path.splitext(entry)
            extension = ext.lower().lstrip('.') if ext else ''

            # Относительный путь считаем ОТ ИСХОДНОГО КОРНЯ
            rel = os.path.relpath(full, root_directory)

            if verbose:
                print("  " * (_depth + 1) + f"  [ФАЙЛ] {entry} ({size} байт)")

            result.append({
                'full_path': full,
                'rel_path': rel,
                'filename': entry,
                'extension': extension,
                'size_bytes': size,
                'modified': mtime
            })
    return result