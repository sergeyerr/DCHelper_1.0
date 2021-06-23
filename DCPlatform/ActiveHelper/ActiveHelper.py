import pandas as pd
from ActiveHelper.TaskSelector import get_emb, get_task_type
from ActiveHelper.ColumnChecker import check_column_feasibility
from ActiveHelper.ColumnSelector import get_columns_in_query
from ActiveHelper.MethodsSuggester import suggest_methods
from ActiveHelper.OntologyRecomender import find_methods_for_task, find_method_id
from scipy.spatial import distance
from openml.tasks import TaskType
from DataServiceAdapter import DataServiceAdapter
import os

data_service_adapter = DataServiceAdapter(os.getenv('DATA_SERVICE', "localhost:8000"))


class ActiveHelper(object):
    def __init__(self):
        self.data = None
        self.reset()

    def reset(self):
        self.current_state = self.state_0
        self.greeting = True
        # self.stack = []
        # self.data = None
        self.task = None
        self.superv = None
        self.target_col = None
        self.data_id = None
        self.possible_targets = set(
            pd.read_csv('ActiveHelper/target_list.csv')['target'].str.lower().values.reshape(-1))
        self.task_query = None
        self.keywords = {'Начать заново': (self.state_0, get_emb('начать заново')),
                         'В начало диалога': (self.state_0, get_emb('в начало диалога')),
                         }
        #      'Назад' : ,
        #   'К выбору задачи' :,
        #    'К загрузке данных' :
        #    'К выбору целевой колонки' : ,}

    def check_keywords(self, query):
        target = get_emb(str.lower(query))
        for k in self.keywords:
            if distance.cosine(target, self.keywords[k][1]) < 0.2:
                print(k, distance.cosine(target, self.keywords[k][1]))
                return self.keywords[k][0](query, reset=True)
        return None

    # def _back_(self):
    #  if len(stack) == 0:
    #     return 'Вы ещё не совершали операций'
    #  self.data, self.task, self.superv, self.target_col, self.task_query =

    # def _to_task_(self)

    def confirmation_state(self, positive_state=None, negative_state=None, threshold=0.225):
        '''
        Декоратор, позволяющий делать развилку в диалоге на основе подтверждения пользователя
        '''
        if positive_state is None or negative_state is None:
            raise Exception('invalid clause')

        def tmp_confirmation(query):
            # = ['Да', 'Верно', 'Ок', 'ага']
            # negative_vars = ['Нет', 'Неправильно', 'Заново', 'косячно']
            # pos = get_columns_in_query(query, positive_vars, threshold=1, norm=True)
            # neg = get_columns_in_query(query, negative_vars, threshold=1, norm=True)
            positive_emb = get_emb('да, правильно')
            negative_emb = get_emb('нет, не правильно')
            target = get_emb(query)
            pos_dist = distance.cosine(target, positive_emb)
            neg_dist = distance.cosine(target, negative_emb)
            print(pos_dist, neg_dist)
            # if len(pos) == 0 and len(neg) == 0:
            if neg_dist > threshold and pos_dist > threshold:
                return 'Не удалось распознать ответ. Пожалуйста, повторите его'
            # if (2 if len(pos) == 0 else pos[0][1]) > (2 if len(neg) == 0 else neg[0][1]):
            if pos_dist > neg_dist:
                return negative_state(None)
            else:
                return positive_state(None)

        return tmp_confirmation

    def state_0(self, query, reset=False):
        res = ''
        if reset:
            self.reset()
        if self.greeting:
            res += 'Доброго времени суток! \n'
            self.greeting = False
        self.current_state = self.state_task_selection
        res += 'Пожалуйста, загрузите данные, а после опишите задачу, которую хотите решить.'
        return [['reload'], ['text', res]]

    def state_task_selection(self, query: str):
        task_type, desc = get_task_type(query)
        if task_type == None:
            return [['text', 'Простите, я не могу определить задачу. Перефразируйте, пожалуйста, вопрос.']]
        res = 'Я считаю, что вы хотите решить задачу '
        if task_type == TaskType.SUPERVISED_CLASSIFICATION:
            self.current_state = self.state_plea_to_upload_data
            res += 'классификации.'
            self.superv = True
        elif task_type == TaskType.SUPERVISED_REGRESSION:
            self.current_state = self.state_plea_to_upload_data
            res += 'регрессии.'
            self.superv = True
        elif task_type == TaskType.CLUSTERING:
            self.current_state = self.state_plea_to_upload_data
            res += 'кластеризации.'
            self.superv = False
        else:
            raise Exception('Wrong Task for task selection')

        self.task = task_type
        self.task_query = query
        # вот тут развилка для умных пользователей
        target_col = None
        if self.data is not None:
            target_col = self._find_target_cols_in_history()
        if target_col is not None:
            res += f' Также я предполагаю, что вы хотите определять колонку {target_col}. '

            def positive_state(query):
                self.target_col = target_col
                return self.state_find_algos(query)

            self.current_state = self.confirmation_state(positive_state, self.state_after_guess_task_confirmation)
        else:
            self.current_state = self.confirmation_state(self.state_plea_to_upload_data, self.state_0)
        res += ' \nВсё правильно? \n\n'
        return [['text', res], ['text', desc]]

    def state_after_guess_task_confirmation(self, query):
        if self.data is None:
            raise Exception('this state should be preceded by task selection with data, wtf')

        self.current_state = self.confirmation_state(self.state_plea_to_specify_target_col, self.state_0)
        return [['text', 'А задачу-то я угадал?']]

    def state_plea_to_upload_data(self, query: str):
        if self.data is not None:
            return self.state_check_data_download(None)
        self.current_state = self.state_check_data_download
        return [['text', 'Загрузите, пожалуйста, данные. Это можно сделать с помощью кнопки upload data.']]

    def state_check_data_download(self, query: str):
        if self.data is None:
            return [['text', 'Данные не удалось распознать. Пожалуйста, загрузите их в формате .csv и кодировке utf-8.']]
        else:
            if self.superv:
                return self.state_try_extract_target_col(None)
            else:
                return self.state_find_algos(None)

    def _find_target_cols_in_history(self):
        # поиск в предыдущем запросе таргета
        found_cols = get_columns_in_query(self.task_query, [x for x in self.data.columns if len(x) > 3])
        if len(found_cols) != 0:
            cols = [x[0] for x in found_cols]
            for col in cols:
                if self.task in check_column_feasibility(self.data[col]):
                    return col
        # поиск таргета среди истории
        possible_targs_ = set(self.data.columns.str.lower()).intersection(self.possible_targets)
        possible_targs = set()
        for col in self.data.columns:
            if str.lower(col) in possible_targs_:
                possible_targs.add(col)
        for col in possible_targs:
            if self.task in check_column_feasibility(self.data[col]):
                return col
        return None

    def state_try_extract_target_col(self, query=None):
        if self.task_query is not None:
            col = self._find_target_cols_in_history()
            if col:
                def positive_state(query):
                    self.target_col = col
                    return self.state_find_algos(query)

                self.current_state = self.confirmation_state(positive_state, self.state_plea_to_specify_target_col)
                return [['text', f'Я предполагаю, что вы хотите определять колонку {col}. Я прав?']]
            else:
                return self.state_plea_to_specify_target_col(query)
        else:
            raise Exception('why task query is None?? ')

    def state_plea_to_specify_target_col(self, query: str):
        # if self.target_col is not None:
        #  print('fix plea')
        # return state_find_target_col()
        # if query is not None:

        # else:
        self.current_state = self.state_find_target_col
        return [['text',  'Пожалуйста, напишите целевую колонку, которую хотите научится определять']]

    def state_find_target_col(self, query: str):
        if query != None:
            found_cols = get_columns_in_query(query, list(self.data.columns))
            if len(found_cols) == 0:
                return [['text', 'Не удалось найти упоминание колонки в запросе. Проверьте название колонки']]
            else:
                cols = [x[0] for x in found_cols]
                for col in cols:
                    if self.task in check_column_feasibility(self.data[col]):
                        def positive_state(query):
                            self.target_col = col
                            return self.state_find_algos(query)

                        self.current_state = self.confirmation_state(positive_state,
                                                                     self.state_plea_to_specify_target_col)
                        return [['text', f'Я считаю, что Вы хотите определять колонку {col}. Я прав?']]
                return [['text', f'Ни одна из колонок {",".join(cols)}\n не подходит под выбранную задачу. \nПожалуйста,'
                                 f'проверьте запрос или данные ']]

    def state_find_algos(self, query: str):
        if self.task is None:
            raise Exception('No task selected')
        if self.data is None or self.data_id is None:
            raise Exception('No dataset selected')
        if self.superv and self.target_col == None:
            raise Exception('No target col selected')
        # лолка, не те данные
        data_features = data_service_adapter.get_metafeatures_of_datasets([self.data_id]).to_dict('records')[0]
       # print(data_features)
        del data_features['openml_id']
        del data_features['data_table']
        del data_features['name']
        del data_features['id']
        methods = suggest_methods(self.task, self.data, data_features, self.target_col)
        methods = [x[0] for x in methods]
        ont_methods = find_methods_for_task(self.task)
        res = []
        if len(methods) == 0 and len(ont_methods) == 0:
            return [['text', 'Не удаётся найти подходящие методы для вашей задачи. Если данное сообщение вылезло в данной ' \
                   'версии помощника, напиши автору ']]
        if len(methods) != 0:
            #methods_str = "\n".join(methods[:3])
            #топ 3
            methods = methods[:3]
            res.append(['text', 'Эти методы должны хорошо работать на ваших данных:\n'])
            for method in methods:
                method_id = find_method_id(method)
                if method_id is not None:
                    res.append(['method_link', method, method_id])
                else:
                    res.append(['text', method])
            #res = f'Эти методы должны хорошо работать на ваших данных:\n {methods_str}'

            if len(ont_methods) > 0:
                res.append(['text', '\n Также, '])
            # return 'В системе нет подходящих методов под задачу'
        if len(ont_methods) != 0:
            ont_methods_filtered = list(set([x[0] for x in ont_methods]) - set(methods))
            ont_methods = [x for x in ont_methods if x[0] in ont_methods_filtered]
            ont_methods = ont_methods[:3]
            res.append(['text', 'Я предлагаю Вам попробовать алгоритмы:'])
            for method in ont_methods:
                res.append(['method_link', method[0], method[1]])
        self.current_state = self.end_state
        return res

    def end_state(self, query: str):
        return [['text', 'Если хотите начать заново, напишите "Начать заново"']]

    def process_query(self, query: str) -> list:
        tmp_res = self.check_keywords(str.lower(query))
        if tmp_res is None:
            return self.current_state(str.lower(query))
        return tmp_res
