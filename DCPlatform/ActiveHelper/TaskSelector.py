from sentence_transformers import SentenceTransformer
from openml.tasks import TaskType
from os import listdir
from os.path import join
from sklearn.neighbors import NearestNeighbors
from scipy.spatial import distance

# иницилизация нейронной сети
model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1')
# массивы под тексты
classification = []
regression = []
clustering = []


def get_emb(text):
    return model.encode(text)


for f in listdir(r'ActiveHelper/data_texts/supervised/classification'):
    with open(join(r'ActiveHelper/data_texts/supervised/classification', f), 'r', encoding='utf-8') as f:
        classification.append(f.read())
for f in listdir(r'ActiveHelper/data_texts/supervised/regression'):
    with open(join(r'ActiveHelper/data_texts/supervised/regression', f), 'r', encoding='utf-8') as f:
        regression.append(f.read())
for f in listdir(r'ActiveHelper/data_texts/unsupervised/clustering'):
    with open(join(r'ActiveHelper/data_texts/unsupervised/clustering', f), 'r', encoding='utf-8') as f:
        clustering.append(f.read())
classification_embeddings = [get_emb(x) for x in classification]
regression_embeddings = [get_emb(x) for x in regression]
clustering_embeddings = [get_emb(x) for x in clustering]


def get_task_type(text: str, threshold=0.75):
    """
    Возвращает задачу МО для запроса + наиболее близкое описание
    Если запрос находится синтаксически далеко от описания задач, то возвращается None
    """

    label_map = {TaskType.SUPERVISED_CLASSIFICATION: classification_embeddings, TaskType.SUPERVISED_REGRESSION: regression_embeddings,
                 TaskType.CLUSTERING: clustering_embeddings}
    label_map_ = {TaskType.SUPERVISED_CLASSIFICATION: classification, TaskType.SUPERVISED_REGRESSION: regression,
                  TaskType.CLUSTERING: clustering}
    labels = []
    X = [y for x in label_map.values() for y in x]
    X_texts = [y for x in label_map_.values() for y in x]
    for k in label_map:
        labels += [k for x in range(len(label_map[k]))]
    neigh = NearestNeighbors(n_neighbors=5, radius=0.2, metric=distance.cosine)
    fitted = neigh.fit(X, labels)
    emb = get_emb(text)
    dists, indecies = fitted.kneighbors([emb])
    res = list(filter(lambda x: x[0] < threshold, zip(dists.reshape(-1), indecies.reshape(-1))))
    if len(res) == 0:
        return None, None
    else:
        # counter = dict()
        # for k in label_map:
        # counter[k] = 0
        return labels[res[0][1]], X_texts[res[0][1]]
        # for _, ind in res:
        #    counter[labels[ind]] += 1
        # print(counter)