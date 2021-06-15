from ont_mapping import dfs_edges
from app import datasets_ont
def SortedDict(prev):
    res = prev
    if 'nodes' in prev:
        res['nodes'] = sorted(prev['nodes'], key=lambda x: str.lower(x['text']))
        for i in range(len(res['nodes'])):
            res['nodes'][i] = SortedDict(res['nodes'][i])
    return res

def make_branch(ontology, root_query = '', input_edges_dfs = [], output_edges_dfs = [], pass_cycles=False, remove_copies=True, sorted=True, node = None, mark_methods = True):
    if node is None:
        tmp = ontology.select_nodes(root_query)
        if len(tmp) == 0:
            return {}
        node = tmp[0]
    edges = dfs_edges(node, input_edges_dfs, output_edges_dfs, pass_cycles)
    res = {'text': node.name, 'initId': node.id, 'nodes': [], 'annotation': node.attributes['<description>']
                                                            if '<description>' in node.attributes else None}
    if mark_methods:
        res['isMethod'] = False
    nodes_dict = {node: res}
    for edge in edges:
        origin = edge.source
        dest = edge.dest
        if edge.name in output_edges_dfs:  # in case of opposite direction swap needed
            origin, dest = dest, origin
        if origin not in nodes_dict:
            nodes_dict[origin] = {'text': origin.name, 'initId': origin.id, 'annotation': origin.attributes['<description>']
                                                            if '<description>' in origin.attributes else None}
            if mark_methods:
                if (edge.name == 'use' or edge.name == 'a_part_of') and edge.name in input_edges_dfs:
                    nodes_dict[origin]['isMethod'] = True
                elif 'isMethod' not in nodes_dict[origin]:
                    nodes_dict[origin]['isMethod'] = False
        if 'nodes' not in nodes_dict[dest]:
            nodes_dict[dest]['nodes'] = []
        if remove_copies:
            if nodes_dict[origin] not in nodes_dict[dest]['nodes']:
                nodes_dict[dest]['nodes'].append(nodes_dict[origin])
        else:
            nodes_dict[dest]['nodes'].append(nodes_dict[origin])
    if sorted:
        res = SortedDict(res)
    return res


def find_lib(node):
    edge = node.has_output_relation('a_part_of')
    if not edge:
        return None
    return edge.dest


import os
def find_dataset(name):
    if not datasets_ont:
        return False
    head, tail = os.path.split(name)
    res = datasets_ont.select_nodes(f'node.name in "{tail}"')
    if len(res) == 0:
        return False
    return res[0]

def supervised(ontology, node):
    edges = dfs_edges(node, [], ['use', 'used_for', 'is_a'])
    for edge in edges:
        if 'Supervised' in edge.dest.name:
            return True
    return False

def is_clustering(ontology, node):
    edges = dfs_edges(node, [], ['use', 'used_for', 'is_a'])
    for edge in edges:
        if 'Clustering' in edge.dest.name:
            return True
    return False