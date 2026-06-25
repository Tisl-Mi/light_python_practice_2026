"""
Модуль сравнения исходной папки с резервной копией.
Использует scanner.scan_directory для обеих папок,
затем сравнивает наборы относительных путей и содержимое файлов.
"""

import os
from scanner import scan_directory
from hasher import compute_hash

def compare_folders(source_root, backup_root):
    """
    Сравнивает две папки.
    Возвращает три списка:
      - missing  : файлы, которые есть в source, но отсутствуют в backup
      - extra    : файлы, которые есть в backup, но отсутствуют в source
      - changed  : файлы с одинаковым путём, но разным содержимым
                   (сначала сравнивается размер, если совпадает – хеш)
    """
    # Получаем полные списки файлов из обеих папок
    source_files = scan_directory(source_root)
    backup_files = scan_directory(backup_root)

    # Превращаем в словари {относительный_путь: полная_информация}
    source_dict = {f['rel_path']: f for f in source_files}
    backup_dict = {f['rel_path']: f for f in backup_files}

    source_paths = set(source_dict.keys())
    backup_paths = set(backup_dict.keys())

    # Отсутствующие и лишние
    missing = sorted(source_paths - backup_paths)
    extra   = sorted(backup_paths - source_paths)

    # Общие файлы – проверяем изменения
    common = source_paths & backup_paths
    changed = []
    for rel in sorted(common):
        src_f = source_dict[rel]
        bck_f = backup_dict[rel]

        # Быстрая проверка по размеру
        if src_f['size_bytes'] != bck_f['size_bytes']:
            changed.append(rel)
            continue

        # Размеры совпали – сравниваем хеши
        h1 = compute_hash(src_f['full_path'])
        h2 = compute_hash(bck_f['full_path'])
        if h1 is None or h2 is None or h1 != h2:
            changed.append(rel)

    return missing, changed, extra