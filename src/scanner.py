import os

def scan_directory(directory):
    """
    Рекурсивно обходит directory и возвращает список полных путей ко всем файлам.
    """
    result = []
    try:
        entries = os.listdir(directory)
    except PermissionError:
        # Пропускаем папки без прав доступа
        return result

    for entry in entries:
        full_path = os.path.join(directory, entry)
        if os.path.isdir(full_path):
            # Рекурсивно заходим в поддиректорию
            result.extend(scan_directory(full_path))
        else:
            result.append(full_path)
    return result