import os
import fnmatch

class ExtensionFilter:
    def __init__(self, extensions):
        self.extensions = set(ext.lower() for ext in extensions)

    def apply(self, filepath):
        _, ext = os.path.splitext(filepath)
        return ext.lower().lstrip('.') in self.extensions

class PatternFilter:
    def __init__(self, pattern):
        self.pattern = pattern

    def apply(self, filepath):
        return fnmatch.fnmatch(os.path.basename(filepath), self.pattern)

def apply_filters(file_list, filters):
    """Последовательно применяет все фильтры к списку путей."""
    for f in filters:
        file_list = [fp for fp in file_list if f.apply(fp)]
    return file_list