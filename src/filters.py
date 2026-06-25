"""
Модуль фильтрации файлов.
Содержит:
  - ExtensionFilter – отбор по расширению
  - PatternFilter   – отбор по glob-шаблону имени (fnmatch)
  - apply_filters   – вспомогательная функция для последовательного применения фильтров
"""

import os
import fnmatch

class ExtensionFilter:
    """
    Фильтр по расширению.
    Принимает список расширений (без точки), например ['txt', 'py'].
    """
    def __init__(self, extensions):
        # Сохраняем расширения в нижнем регистре для единообразия
        self.extensions = set(ext.lower() for ext in extensions)

    def apply(self, filepath):
        """
        Проверяет, подходит ли файл под заданные расширения.
        filepath – относительный или абсолютный путь (используется только расширение).
        Возвращает True/False.
        """
        _, ext = os.path.splitext(filepath)
        return ext.lower().lstrip('.') in self.extensions

class PatternFilter:
    """
    Фильтр по шаблону имени файла (fnmatch).
    Пример шаблона: '*.py', 'test_*', 'README.*'.
    """
    def __init__(self, pattern):
        self.pattern = pattern

    def apply(self, filepath):
        """
        Проверяет, соответствует ли имя файла (без пути) заданному шаблону.
        filepath – путь, из которого будет взято только имя файла.
        """
        return fnmatch.fnmatch(os.path.basename(filepath), self.pattern)

def apply_filters(file_list, filters):
    """
    Применяет список объектов-фильтров к списку путей.
    Каждый фильтр должен иметь метод apply(filepath).
    Возвращает отфильтрованный список.
    """
    for f in filters:
        file_list = [fp for fp in file_list if f.apply(fp)]
    return file_list