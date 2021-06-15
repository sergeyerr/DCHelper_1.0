from nltk.stem.snowball import SnowballStemmer
from langdetect import detect
from Levenshtein import distance
from collections import deque

import re
from nltk.corpus import stopwords


class QueryProcessor:
    def __init__(self, ont):
        self.stemmers = {'en': SnowballStemmer('english'), 'ru': SnowballStemmer('russian')}
        self.stop_words_ = {'en': set(stopwords.words('english')), 'ru': set(stopwords.words('russian'))}
        self.regex = re.compile('[,\.!?-_ ]')
        self.normed_nodes = {}
        self.synonym_nodes = {}
        self.max_answers = 10
        for ind, node in ont.__nodes__.items():
            name = node.name.lower()
            if name == 'init':
                continue
            name = self.regex.sub('', name)
            self.normed_nodes[name] = node
            syn_edge = node.has_input_relation('synonym')
            if syn_edge:
                syn_name = syn_edge.source.name
                syn_name = syn_name.lower()
                syn_name = self.regex.sub('', syn_name)
                self.synonym_nodes[name] = syn_name

    def process_query(self, query):
        query = query.lower()
        lang = detect(query)
        if lang not in ['en', 'ru']:
            lang = 'en'
        stemmer = self.stemmers[lang]
        stop_words = self.stop_words_[lang]
        # tokenizing
        query = [stemmer.stem(self.regex.sub('', item)) for item in query.split(' ') if item not in stop_words]
        query = [x for x in query if len(x) > 0]
        highlighted = {}
        # selecting nodes from tokens
        for token in query:
            tmp = []
            for name, node in self.normed_nodes.items():
                if token in name or distance(token, name) <= 2:
                    tmp.append(name)
            for name in tmp:
                if name not in highlighted:
                    highlighted[name] = 0
                highlighted[name] += 1
        # synonym collection
        highlighted_ = highlighted.copy()
        for name in highlighted:
            if name in self.synonym_nodes:
                if self.synonym_nodes[name] not in highlighted_:
                    highlighted_[self.synonym_nodes[name]] = 0
                highlighted_[self.synonym_nodes[name]] += highlighted_.pop(name)
        highlighted = highlighted_
        if len(highlighted) == 0:
            return []
        # BFS, using input edges + merging
        visited_nodes = {}
        leafs = set()
        for name, weight in highlighted.items():
            q = deque()
            s = set()
            node = self.normed_nodes[name]
            if node not in visited_nodes:
                visited_nodes[node] = {'min_dist': 100500, 'weight': 0}
            visited_nodes[node]['min_dist'] = min(visited_nodes[node]['min_dist'], 0)
            visited_nodes[node]['weight'] += weight
            q.append((node, 0))
            while len(q) > 0:
                cur, dist = q.popleft()
                if len(cur.input_relations) == 0:
                    leafs.add(cur)
                for ind, edge in cur.input_relations.items():
                    source = edge.source
                    if source not in visited_nodes:
                        visited_nodes[source] = {'min_dist': 100500, 'weight': 0}
                    if source not in s:
                        # сделать так, чтобы методы не влияли на min_dist
                        visited_nodes[source]['min_dist'] = min(visited_nodes[source]['min_dist'], dist + 1)
                        visited_nodes[source]['weight'] += weight
                        q.append((source, dist + 1))
                        s.add(source)

        # reduction of leafs cost
        for leaf in leafs:
            visited_nodes[leaf]['weight'] = visited_nodes[leaf]['weight'] - 1

        if len(visited_nodes) == 0:
            return []

        max_weight = max(visited_nodes.values(), key=lambda x: x['weight'])['weight']
        res = [(k.name, k.id, v['min_dist']) for k, v in visited_nodes.items() if
               v['weight'] == max_weight]
        res.sort(key=lambda x: x[2], reverse=False)
        return [(x[1], x[0]) for x in res[:self.max_answers]]

