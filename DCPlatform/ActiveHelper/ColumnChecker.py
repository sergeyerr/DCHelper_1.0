import pandas as pd
from openml.tasks import TaskType
def check_column_feasibility(col : pd.Series, classification_threshold = 20) -> set:
    '''
    Возвращает список задач, под которые подходит колонка в качестве целевой
    '''
    res = set()
    if col.dtype == 'float64' or \
        col.dtype == 'int64' or \
        col.dtype == 'float32' or col.dtype == 'int32':
        res.add(TaskType.SUPERVISED_REGRESSION)
    if len(pd.unique(col)) < classification_threshold:
        classification = True
        res.add(TaskType.SUPERVISED_CLASSIFICATION)
    return res