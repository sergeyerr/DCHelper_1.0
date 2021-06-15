import json
from collections import deque


class Node(object):
    def __init__(self, node_id, name, pos_x, pos_y, attributes={}):
        self.id = node_id
        self.name = name
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.attributes = attributes
        self.output_relations = {}
        self.input_relations = {}

    def has_input_relation(self, rel_name):
        for edge in self.input_relations.values():
            if edge.name == rel_name:
                return edge
        return False

    def has_output_relation(self, rel_name):
        for edge in self.output_relations.values():
            if edge.name == rel_name:
                return edge
        return False


class Relation(object):
    def __init__(self, edge_id, name, source, destination, attributes={}):
        self.id = edge_id
        self.name = name
        self.source = source
        self.dest = destination
        self.attributes = attributes


def dfs_edges(node, passing_in=[], passing_out=[], pass_cycles=False):
    answer = []
    stack = deque()
    visited = set()
    stack.append([node, 0, 0])  # stack element: node, input_index, output_index
    backtrack = False
    while len(stack) > 0:
        node, input_ind, output_ind = stack[-1]
        next_node = False
        if node in visited and not backtrack:
            if pass_cycles:
                stack.pop()
                continue
            else:
                raise Exception('Cycle detected!')
        backtrack = False
        visited.add(node)
        list_of_input_keys = list(node.input_relations.keys())
        list_of_output_keys = list(node.output_relations.keys())

        while input_ind < len(list_of_input_keys):
            key = list_of_input_keys[input_ind]
            relation = node.input_relations[key]
            if relation.name in passing_in:
                next_node = True
                stack[-1][1] = input_ind + 1
                answer.append(relation)
                stack.append([relation.source, 0, 0])
                break
            input_ind += 1
        if next_node:
            continue

        while output_ind < len(list_of_output_keys):
            key = list_of_output_keys[output_ind]
            relation = node.output_relations[key]
            if relation.name in passing_out:
                next_node = True
                stack[-1][2] = output_ind + 1
                answer.append(relation)
                stack.append([relation.dest, 0, 0])
                break
            output_ind += 1
        if next_node:
            continue

        backtrack = True
        stack.pop()
        visited.remove(node)
    return answer


class Ontology(object):
    def __init__(self, file=None, json_string=None):
        self.__nodes__ = {}
        self.__relations__ = {}
        if file:
            self._load_from_json(file_path=file)
        elif json_string:
            self._load_from_json(json_string=json_string)

    def _load_from_json(self, file_path=None, json_string=None):
        if json_string:
            data = json.loads(json_string)
            if type(data) == str:  # it is working
                data = json.loads(data)
        else:
            with open(file_path, "r", encoding='utf-8') as read_file:
                data = json.load(read_file)

        for node in data['nodes']:
            self.__nodes__[node['id']] = Node(node['id'], node['name'], node['position_x'], node['position_y'],
                                              node['attributes'])
        for rel in data['relations']:
            source = self.__nodes__[rel['source_node_id']]
            dest = self.__nodes__[rel['destination_node_id']]
            self.__relations__[rel['id']] = Relation(rel['id'], rel['name'], source, dest,
                                                     rel['attributes'])
            source.output_relations[rel['id']] = self.__relations__[rel['id']]
            dest.input_relations[rel['id']] = self.__relations__[rel['id']]

    def select_nodes(self, expr):
        answer = []
        for node in self.__nodes__.values():
            if eval(expr):
                answer.append(node)
        return answer
