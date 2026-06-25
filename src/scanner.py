"""
Рекурсивный обход папок БЕЗ использования os.walk.
Использует os.listdir + рекурсивные вызовы.
Собирает словарь с метаданными каждого файла:
  - full_path   : абсолютный путь
  - rel_path    : путь относительно корня сканирования
  - filename    : имя файла
  - extension   : расширение без точки (в нижнем регистре)
  - size_bytes  : размер в байтах
  - modified    : время последней модификации (timestamp)
"""

import os

def scan_directory(directory, root_directory=None, verbose=False, _depth=0):
    """
    Аргументы:
        directory      – текущая просматриваемая папка (меняется при рекурсии)
        root_directory – исходная корневая папка (нужна для вычисления относительных путей)
        verbose        – печатать ли дерево папок
        _depth         – глубина рекурсии (для отступов при verbose)

    Возвращает:
        список словарей с информацией о каждом найденном файле
    """
    # При первом вызове запоминаем корень
    if root_directory is None:
        root_directory = directory

    result = []

    try:
        entries = os.listdir(directory)          # получаем содержимое папки
    except PermissionError:
        if verbose:
            # Выводим закрытую папку с отступом
            print("  " * _depth + f"[ЗАКРЫТ] {directory}")
        return result

    # Печатаем текущую папку, если verbose
    if verbose:
        print("  " * _depth + f"[ПАПКА] {directory}")

    for entry in entries:
        full = os.path.join(directory, entry)    # полный путь

        if os.path.isdir(full):
            # РЕКУРСИВНЫЙ ВЫЗОВ: заходим в подпапку глубже
            result.extend(scan_directory(full, root_directory, verbose, _depth + 1))
        else:
            # Это файл – собираем метаданные
            try:
                stat = os.stat(full)
                size = stat.st_size
                mtime = stat.st_mtime
            except OSError:
                size = 0
                mtime = 0

            # Расширение без точки (если есть)
            _, ext = os.path.splitext(entry)
            extension = ext.lower().lstrip('.') if ext else ''

            # Относительный путь ОТ ИСХОДНОГО КОРНЯ
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