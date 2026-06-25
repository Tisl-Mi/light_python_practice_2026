import sys
import os
from scanner import scan_directory
from filters import ExtensionFilter, PatternFilter, apply_filters
import db

def main():
    if len(sys.argv) < 2:
        print("Использование: python main.py <путь> [--ext py txt] [--name '*.py']")
        sys.exit(1)

    root = sys.argv[1]

    # Простейший парсинг аргументов
    extensions = []
    name_pattern = None
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
        else:
            i += 1

    print(f"Сканируем папку: {root}")

    # 1. Рекурсивный обход
    all_files = scan_directory(root)
    print(f"Всего файлов: {len(all_files)}")

    # 2. Собираем фильтры
    filters = []
    if extensions:
        filters.append(ExtensionFilter(extensions))
    if name_pattern:
        filters.append(PatternFilter(name_pattern))

    # 3. Применяем фильтры
    filtered_files = apply_filters(all_files, filters)
    print(f"После фильтрации: {len(filtered_files)}")

    # 4. Вывод отфильтрованных файлов
    for fpath in filtered_files:
        rel = os.path.relpath(fpath, root)
        print(rel)

    # 5. Пока только инициализируем БД (без сохранения файлов)
    db.init_db()

if __name__ == "__main__":
    main()