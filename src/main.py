"""
Точка входа в консольный индексатор.
Принимает путь к папке и набор опций через командную строку.
Использует argparse, чтобы было понятно, какие параметры доступны.

Примеры запуска:
   python src/main.py /путь/к/папке
   python src/main.py /путь/к/папке --ext txt py --hash --duplicates --verbose
   python src/main.py /путь/к/папке --backup /путь/к/бэкапу
"""

import argparse
import os
import sys
from scanner import scan_directory
from filters import ExtensionFilter, PatternFilter
import db
import hasher
import backup

def main():
    # ---------- НАСТРОЙКА ARGPARSE ----------
    parser = argparse.ArgumentParser(
        description="Консольный индексатор папок (полный вариант)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Обязательный позиционный аргумент — путь к папке
    parser.add_argument(
        "path",
        help="Путь к сканируемой папке (например, C:\\Users\\User\\Desktop\\test)"
    )

    # Фильтр по расширениям (можно несколько)
    parser.add_argument(
        "--ext", nargs="+",
        help="Фильтр по расширениям (без точки). Пример: --ext txt py"
    )

    # Фильтр по шаблону имени (fnmatch)
    parser.add_argument(
        "--name",
        help="Фильтр по шаблону имени (fnmatch). Пример: --name '*.py'"
    )

    # Показывать дерево папок во время обхода
    parser.add_argument(
        "--verbose", action="store_true",
        help="Показывать дерево папок (рекурсию)"
    )

    # Вычислить хеши для всех найденных файлов
    parser.add_argument(
        "--hash", action="store_true",
        help="Вычислить и сохранить SHA-256 хеши файлов"
    )

    # Показать дубликаты (автоматически включает --hash)
    parser.add_argument(
        "--duplicates", action="store_true",
        help="Показать группы дубликатов (требует --hash)"
    )

    # Размер блока для чтения файла (чанка) в байтах
    parser.add_argument(
        "--chunk-size", type=int, default=2*1024*1024*1024,
        help="Размер чанка для хеширования в байтах (по умолчанию 2 ГБ)"
    )

    # Путь к резервной копии для сравнения
    parser.add_argument(
        "--backup",
        help="Путь к резервной копии для сравнения"
    )

    # Парсим аргументы командной строки
    args = parser.parse_args()

    # ---------- ПРОВЕРКА ПАПКИ ----------
    root = os.path.abspath(args.path)      # абсолютный путь
    if not os.path.isdir(root):
        print(f"Ошибка: {root} не является папкой")
        sys.exit(1)

    print(f"Сканируем папку: {root}")

    # ---------- БАЗА ДАННЫХ ----------
    db.init_db()          # создаст data/app.db и таблицы, если их нет

    # ---------- РЕКУРСИВНЫЙ ОБХОД ----------
    print("\n--- Дерево папок (source) ---")
    # verbose=True печатает [ПАПКА] и [ФАЙЛ] с отступами
    source_files = scan_directory(root, verbose=args.verbose)
    print(f"--- Конец дерева ---\nВсего файлов в исходной: {len(source_files)}")

    # ---------- ФИЛЬТРАЦИЯ ----------
    filters = []
    if args.ext:
        ext_filter = ExtensionFilter(args.ext)
        filters.append(ext_filter)
        print(f"Активен фильтр по расширениям: {args.ext}")
    if args.name:
        name_filter = PatternFilter(args.name)
        filters.append(name_filter)
        print(f"Активен фильтр по имени: {args.name}")

    # Применяем фильтры к каждому файлу (последовательно)
    filtered = []
    rejected_by_ext = 0
    rejected_by_name = 0
    for f in source_files:
        ok = True
        # Проверка расширения (если фильтр задан)
        if args.ext and not ext_filter.apply(f['rel_path']):
            rejected_by_ext += 1
            ok = False
        # Проверка имени (если фильтр задан)
        if ok and args.name and not name_filter.apply(f['rel_path']):
            rejected_by_name += 1
            ok = False
        if ok:
            filtered.append(f)

    total_rejected = len(source_files) - len(filtered)
    print(f"После фильтрации: {len(filtered)} (отсеяно {total_rejected})")
    if args.ext:
        print(f"  Отсеяно по расширению: {rejected_by_ext}")
    if args.name:
        print(f"  Отсеяно по шаблону имени: {rejected_by_name}")

    # ---------- СОХРАНЕНИЕ В БД ----------
    session_id = db.create_session(root)          # новая сессия в scan_sessions
    db.save_files(session_id, filtered)           # записываем все файлы в таблицу files
    print(f"Сохранено в БД (сессия {session_id})")

    # ---------- ВЫВОД ОТФИЛЬТРОВАННОГО СПИСКА ----------
    if len(filtered) <= 50:
        print("\n--- Список отфильтрованных файлов ---")
        for f in filtered:
            print(f"{f['rel_path']}  ({f['size_bytes']} байт)")
    else:
        print("(файлов > 50, список не выводится)")

    # ---------- ХЕШИРОВАНИЕ (ЕСЛИ ЗАПРОШЕНО) ----------
    if args.hash or args.duplicates:
        print("\n=== Вычисление хешей ===")
        # Получаем из БД все файлы текущей сессии
        db_files = db.get_files_by_session(session_id)
        for file_id, rel_path, _, _, _, _, old_hash in db_files:
            full = os.path.join(root, rel_path)   # восстанавливаем полный путь
            h = hasher.compute_hash(full, args.chunk_size)  # хеширование чанками
            if h:
                db.update_hash(file_id, h)        # сохраняем хеш в БД
                print(f"  {rel_path} -> {h[:12]}...")
            else:
                print(f"  {rel_path} -> ОШИБКА")
        print("Хеши сохранены.")

    # ---------- ПОИСК ДУБЛИКАТОВ (ЕСЛИ ЗАПРОШЕНО) ----------
    if args.duplicates:
        print("\n=== Поиск дубликатов ===")
        dups = db.find_duplicates(session_id)     # SQL-запрос группировки по хешу
        if not dups:
            print("Дубликаты не найдены.")
        else:
            for hash_val, paths in dups:
                print(f"\nГруппа (hash={hash_val[:12]}...):")
                for p in paths:
                    print(f"  - {p}")

    # ---------- СРАВНЕНИЕ С РЕЗЕРВНОЙ КОПИЕЙ (ЕСЛИ ЗАДАН --backup) ----------
    if args.backup:
        print("\n" + "=" * 50)
        print(f"Сравнение с резервной копией: {args.backup}")
        missing, changed, extra = backup.compare_folders(root, args.backup)

        print("\nРезультаты сравнения:")
        print(f"  Отсутствует в бэкапе (missing): {len(missing)}")
        for m in missing:
            print(f"    - {m}")
        print(f"  Изменено (changed): {len(changed)}")
        for c in changed:
            print(f"    - {c}")
        print(f"  Лишние в бэкапе (extra): {len(extra)}")
        for e in extra:
            print(f"    - {e}")

        # Сохраняем отчёт в backup_reports
        db.save_backup_report(root, args.backup, missing, changed, extra)
        print("\nОтчёт сохранён в базу данных.")
        print("=" * 50)

# Стандартная конструкция для запуска main()
if __name__ == "__main__":
    main()