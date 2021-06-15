from ont_mapping import Ontology, dfs_edges
from openml.tasks import TaskType


ont = Ontology(file='ActiveHelper/python_v.0.7.ont')
mappind_to_nodes = {TaskType.SUPERVISED_CLASSIFICATION : 'discrete variable(classification)',
                    TaskType.SUPERVISED_REGRESSION : 'continuous variable(Regression)',
                    TaskType.CLUSTERING : 'Clustering'}


def find_methods_for_task(task : TaskType):
    init_node = ont.select_nodes(f'node.name == "{mappind_to_nodes[task]}"')[0]
    algo_nodes = [x.source for x in dfs_edges(init_node, passing_in=['used_for'])]
    methods = []
    for algo in algo_nodes:
        methods += [x.source.name for x in dfs_edges(algo, passing_in=['use'])]
    return methods