import sys
import os
from scanner import scan_directory
from filters import ExtensionFilter, PatternFilter, apply_filters
import db

def main():
    if len(sys.argv) < 2:
        print("Использование: python main.py <путь> [--ext py txt] [--name '*.py'] [--verbose]")
        sys.exit(1)

    root = sys.argv[1]

    # Простейший парсинг аргументов
    extensions = []
    name_pattern = None
    verbose = False
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--ext':
            i += 1
            while i < len(sys.argv) and not sys.argv[i].startswith('--'):
                extensions.append(sys.argv[i])
                i += 1
        elif sys.argv[i] == '--name':
            i += 1
            if i < len(sys.argv):
                name_pattern = sys.argv[i]
                i += 1
        elif sys.argv[i] == '--verbose':
            verbose = True
            i += 1
        else:
            i += 1

    print(f"Сканируем папку: {root}")

    # 1. Инициализация БД
    db.init_db()

    # 2. Рекурсивный обход (с показом дерева, если verbose)
    print("\n--- Дерево папок ---")
    all_files = scan_directory(root, verbose=verbose)
    print(f"--- Конец дерева ---\nВсего файлов: {len(all_files)}")

    # 3. Собираем фильтры
    filters = []
    if extensions:
        filters.append(ExtensionFilter(extensions))
    if name_pattern:
        filters.append(PatternFilter(name_pattern))

    # 4. Применяем фильтры
    filtered = []
    for f in all_files:
        ok = True
        for filt in filters:
            if not filt.apply(f['rel_path']):
                ok = False
                break
        if ok:
            filtered.append(f)

    print(f"После фильтрации: {len(filtered)}")

    # 5. Сохраняем в БД
    session_id = db.create_session(root)
    db.save_files(session_id, filtered)
    print(f"Сохранено в БД (сессия {session_id})")

    # 6. Выводим список файлов (если не слишком много)
    if len(filtered) <= 50:
        print("\n--- Список отфильтрованных файлов ---")
        for f in filtered:
            print(f"{f['rel_path']}  ({f['size_bytes']} байт)")
    else:
        print("(файлов > 50, список не выводится)")

if __name__ == "__main__":
    main()