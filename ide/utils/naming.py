"""naming.py"""


def id_to_name(ide: str):
    """Преобразует строку с идентификатором в название.
    Функция принимает строку, содержащую идентификатор,
    разделённый символом подчёркивания,
    и возвращает строку с преобразованным именем,
    где первые буквы каждого слова заглавные."""
    return " ".join(map(str.capitalize, ide.split("_")))