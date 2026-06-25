import sys
import os
from scanner import scan_directory
from filters import ExtensionFilter, PatternFilter
import db
import hasher
import backup

def main():
    if len(sys.argv) < 2:
        print("Использование: python main.py <путь> [опции]")
        print("  --ext py txt       фильтр по расширениям")
        print("  --name '*.py'      фильтр по шаблону имени")
        print("  --verbose          показывать дерево папок")
        print("  --hash             вычислить и сохранить хеши")
        print("  --duplicates       показать дубликаты (требует --hash)")
        print("  --backup <путь>    сравнить с резервной копией")
        sys.exit(1)

    root = sys.argv[1]
    extensions = []
    name_pattern = None
    verbose = False
    need_hash = False
    show_duplicates = False
    backup_path = None

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--ext':
            i += 1
            while i < len(sys.argv) and not sys.argv[i].startswith('--'):
                extensions.append(sys.argv[i])
                i += 1
        elif arg == '--name':
            i += 1
            if i < len(sys.argv):
                name_pattern = sys.argv[i]
                i += 1
        elif arg == '--verbose':
            verbose = True
            i += 1
        elif arg == '--hash':
            need_hash = True
            i += 1
        elif arg == '--duplicates':
            show_duplicates = True
            i += 1
        elif arg == '--backup':
            i += 1
            if i < len(sys.argv):
                backup_path = sys.argv[i]
                i += 1
        else:
            i += 1

    print(f"Сканируем папку: {root}")

    # 1. Инициализация БД
    db.init_db()

    # 2. Рекурсивный обход
    print("\n--- Дерево папок (source) ---")
    source_files = scan_directory(root, verbose=verbose)
    print(f"--- Конец дерева ---\nВсего файлов в исходной: {len(source_files)}")

    # 3. Фильтрация
    filters = []
    if extensions:
        filters.append(ExtensionFilter(extensions))
    if name_pattern:
        filters.append(PatternFilter(name_pattern))

    filtered = []
    for f in source_files:
        ok = True
        for filt in filters:
            if not filt.apply(f['rel_path']):
                ok = False
                break
        if ok:
            filtered.append(f)

    print(f"После фильтрации: {len(filtered)}")

    # 4. Сохраняем в БД
    session_id = db.create_session(root)
    db.save_files(session_id, filtered)
    print(f"Сохранено в БД (сессия {session_id})")

    # 5. Вывод списка (если не слишком много)
    if len(filtered) <= 50:
        print("\n--- Список отфильтрованных файлов ---")
        for f in filtered:
            print(f"{f['rel_path']}  ({f['size_bytes']} байт)")
    else:
        print("(файлов > 50, список не выводится)")

    # 6. Хеширование и дубликаты
    if need_hash or show_duplicates:
        print("\n=== Вычисление хешей ===")
        db_files = db.get_files_by_session(session_id)
        for file_id, rel_path, _, _, _, _, old_hash in db_files:
            # Находим полный путь из списка filtered (можно было сохранять и id)
            full = os.path.join(root, rel_path)
            h = hasher.compute_hash(full)
            if h:
                db.update_hash(file_id, h)
                print(f"  {rel_path} -> {h[:8]}...")
            else:
                print(f"  {rel_path} -> ОШИБКА")
        print("Хеши сохранены.")

    if show_duplicates:
        print("\n=== Поиск дубликатов ===")
        dups = db.find_duplicates(session_id)
        if not dups:
            print("Дубликаты не найдены.")
        else:
            for hash_val, paths in dups:
                print(f"\nГруппа (hash={hash_val[:12]}...):")
                for p in paths:
                    print(f"  - {p}")

    # 7. Сравнение с резервной копией
    if backup_path:
        print("\n" + "=" * 50)
        print(f"Сравнение с резервной копией: {backup_path}")
        missing, changed, extra = backup.compare_folders(root, backup_path)

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

        db.save_backup_report(root, backup_path, missing, changed, extra)
        print("\nОтчёт сохранён в базу данных.")
        print("=" * 50)

if __name__ == "__main__":
    main()