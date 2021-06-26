from typing import List
from Levenshtein import distance as leven_dist


def get_columns_in_query(query: str, columns: List[str], threshold: int = 3, norm: bool = False) -> List[str]:
    """
    Возвращает найденные названия в запросе с расстоянием Левенштейна, меньшим threshold.
    Отсортированы по возрастанию threshold

    query: str: Пользовательский запрос
    columns: List[str]: список названий колонок из датасета
    threshold: int: максимальная возможное расстояние Левенштена от названия колонок до подстрок запроса
    norm : bool: нужна ли нормировка расстояния на длину слова
    """
    min_dist = 10000000
    res = dict()
    for col in columns:
        for i in range(len(query) - len(col) + 1):
            substr = (str.lower(query[i:i + len(col)])).strip()
            dist = leven_dist(str.lower(col), substr)
            if substr not in res:
                res[col] = dist
    if norm:
        for col in res:
            res[col] /= len(col)
    res = sorted(list(res.items()), key=lambda x: x[1])

    # чтобы короткие колонки не тригерить
    return list(filter(lambda x: x[1] < threshold, res))