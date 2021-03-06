from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from pymfe.mfe import MFE
from openml.tasks import TaskType
import pandas as pd


def get_features(task: TaskType, cached_metafeatures: pd.DataFrame, target: str = None):
    """
    Возвращает метапризнаки данного датасета

    task: TaskType: Тип решаемой задачи машинного обучения
    cached_metafeatures: pd.DataFrame: заранее предпосчитанные признаки датасета
    target: str: при наличии, целевая колонка в датасете для решаемой задачи
    """
    categorical_barrier = 20
    features = {}
    is_superv = task == TaskType.SUPERVISED_CLASSIFICATION or TaskType.SUPERVISED_REGRESSION
    if is_superv and not target:
        raise Exception("not target for supervised task")
    if task == TaskType.SUPERVISED_CLASSIFICATION:
        if len(pd.unique(cached_metafeatures[target])) > categorical_barrier:
            raise Exception('too many values for classification')
        features['MajorityClassSize'] = cached_metafeatures.groupby(target).count().max()[0]
        features['MinorityClassSize'] = cached_metafeatures.groupby(target).count().min()[0]
        features['NumberOfClasses'] = len(cached_metafeatures[target].unique())
    if task == TaskType.SUPERVISED_REGRESSION:
        if cached_metafeatures[target].dtype != 'float64' and \
                cached_metafeatures[target].dtype != 'int64' and \
                cached_metafeatures[target].dtype != 'float32' and cached_metafeatures[target].dtype != 'int32':
            raise Exception('target is not numeric attribute')
        features['target_max'] = cached_metafeatures[target].max()
        features['target_min'] = cached_metafeatures[target].min()
        features['targets_q_0.25'] = cached_metafeatures[target].quantile(0.25)
        features['targets_q_0.5'] = cached_metafeatures[target].quantile(0.5)
        features['targets_q_0.75'] = cached_metafeatures[target].quantile(0.75)
        features['targets_skewness'] = cached_metafeatures[target].skew()
        features['targets_kurtosis'] = cached_metafeatures[target].kurt()
    if is_superv:
        cached_metafeatures = cached_metafeatures.copy().drop([target], axis=1)
    features['NumberOfBinaryFeatures'] = len([col for col in cached_metafeatures if
                                              cached_metafeatures[col].dropna().value_counts().index.isin([0, 1]).all()])
    features['NumberOfFeatures'] = len(cached_metafeatures.columns) - 1 if is_superv else 0
    features['NumberOfInstances'] = len(cached_metafeatures)
    features['NumberOfInstancesWithMissingValues'] = cached_metafeatures.shape[0] - cached_metafeatures.dropna().shape[0]
    features['NumberOfNumericFeatures'] = len(
        cached_metafeatures.select_dtypes(include=['float64', 'int64', 'float32', 'int32']).columns)
    # MFE фичи подсчитываются в дата-сервисе
    # mfe = MFE('all')
    # mfe.fit(data.values)
    # ft = mfe.extract()
    # for k, v in zip(ft[0], ft[1]):
    #     features[k] = v
    return features



# запуски с OpenML
runs = pd.read_csv('ActiveHelper/all_you_need_runs.csv')
class_features = pd.read_csv('ActiveHelper/classification_data.csv')
reg_features = pd.read_csv('ActiveHelper/regression_data.csv')
class_scaler = StandardScaler()
reg_scaler = StandardScaler()
class_features = class_features[class_features['var_mean'] < class_features['var_mean'].quantile(0.8)]
class_features_ = class_scaler.fit_transform(class_features.drop(['did'], axis=1))
reg_features = reg_features[reg_features['var_mean'] < reg_features['var_mean'].quantile(0.8)]
reg_features_ = reg_scaler.fit_transform(reg_features.drop(['did'], axis=1))
class_features[class_features.drop(['did'], axis=1).columns] = class_features_
reg_features[reg_features.drop(['did'], axis=1).columns] = reg_features_


def suggest_methods(task: TaskType, dataset: pd.DataFrame, data_metafeatures : dict, target : str = None) -> list:
    """
    Предлагает методы решения задачи МО для данного датасета

    task: TaskType: задача машинного обучения
    dataset: pd.DataFrame: датасет
    data_metafeatures: dict: предподсчитанные метапризнаки датасета
    target: str: целевая колонка
    """
    def place(x):
        x['place'] = range(1, len(x) + 1)
        return x

    target_features = pd.DataFrame([{**get_features(task, dataset, target), **data_metafeatures}]).dropna(axis=1)
    print(target_features)

    comparison_metric = {TaskType.SUPERVISED_CLASSIFICATION: 'area_under_roc_curve',
                         TaskType.SUPERVISED_REGRESSION: 'mean_absolute_error'}

    if task == TaskType.CLUSTERING:
        raise Exception('alarm')
    if task == TaskType.SUPERVISED_CLASSIFICATION:
        data_features = class_features
        data = data_features[target_features.columns]
        class_scaler.fit(data)
        target_features_ = class_scaler.transform(target_features)
    elif task == TaskType.SUPERVISED_REGRESSION:
        data_features = reg_features
        data = data_features[target_features.columns]
        reg_scaler.fit(data)
        target_features_ = reg_scaler.transform(target_features)

    else:
        raise Exception('alarm')
    target_features[:] = target_features_
    #  target_features = target_features.dropna(axis=1)

    data.loc[:, 'did'] = data_features['did']
    neigh = NearestNeighbors(n_neighbors=len(data) // 3)
    data = data.dropna()
    neigh.fit(data.drop(['did'], axis=1))
    dist, ind = neigh.kneighbors(target_features)
    ind = ind.reshape(-1)
    dist = dist.reshape(-1)
    dists_frame = pd.DataFrame()
    dists_frame['did'] = data.iloc[ind, :]['did']
    dists_frame['dist'] = dist

    req_runs = runs[runs['did'].isin(data.iloc[ind, :]['did'])].copy()
    tmp = req_runs[req_runs[comparison_metric[task]].notna()].groupby(['task_id', 'name'])
    tmp = tmp.apply(lambda x: x.sort_values(ascending=False, by='area_under_roc_curve'))
    # выбираем самые лучшие попытки
    tmp = tmp.reset_index(drop=True).groupby(['task_id', 'name']).first().reset_index()
    # сортируем алгосы по крутости в рамках задачи
    tmp = tmp.groupby(['task_id']).apply(
        lambda x: x.sort_values(ascending=False, by=comparison_metric[task])).reset_index(drop=True)
    # места по крутости на задаче
    tmp = tmp.groupby(['task_id']).apply(lambda x: place(x))
    tmp = tmp.join(dists_frame.set_index('did'), on='did')
    tmp['weighted_place'] = tmp['place'] * tmp['dist']
    tmp = tmp.groupby(['name'])['weighted_place'].mean().dropna()
    tmp = tmp.sort_values()
    return list(zip(tmp.index, list(tmp)))
