import psycopg2
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
import pandas as pd
import math
from typing import List, Tuple
from pymfe.mfe import MFE
import random
import string
from werkzeug.security import generate_password_hash


class PostgresWorker:
    def __init__(self, user, password, default_db='test', host='localhost', reinit_db=False):
        self.user = user
        self.password = password
        self.db = default_db
        self.host = host
        if reinit_db:
            self.__init_db__()
        self.__create_connection__()

        check_query = f"""SELECT datname FROM pg_catalog.pg_database WHERE lower(datname) = lower('{default_db}');"""
        self.cursor.execute(check_query)
        if len(self.cursor.fetchall()) == 0:
            print('creating db...')
            self.__init_db__()
            self.__create_connection__()
        else:
            print('use existing db')

        self.engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}/{self.db}')
        # костыль связанный с тем, что нужно отключать все подключения перед дропом базы
        if reinit_db:
            self.__init_tables__()

    def __del__(self):
        self.cursor.close()
        self.con.close()

    def __create_connection__(self):
        self.con = psycopg2.connect(user=self.user, password=self.password, dbname=self.db, host=self.host)
        self.con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.cursor = self.con.cursor()

    def __init_db__(self):
        con = psycopg2.connect(user=self.user, password=self.password, host=self.host)
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = con.cursor()

        sqlKickUsers = f'''
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{self.db}' -- ← change this to your DB
        AND pid <> pg_backend_pid();'''
        sqlDropDB = f"DROP DATABASE IF EXISTS {self.db};"
        sqlCreateDB = f"create database {self.db};"
        cursor.execute(sqlKickUsers)
        cursor.execute(sqlDropDB)
        cursor.execute(sqlCreateDB)
        cursor.close()
        con.close()

    def __init_tables__(self):
        old_data = pd.read_csv('PostgresWorker/meta_features.csv')
        for col in old_data.columns:
            old_data = old_data.rename({col : col.replace('.', '_')}, axis=1)
        old_data.to_sql('datasets_meta', self.engine, if_exists='replace', index=False)
        self.cursor.execute('ALTER TABLE datasets_meta ADD COLUMN id SERIAL PRIMARY KEY;')
        user_sql = '''CREATE TABLE users(id serial PRIMARY KEY, username VARCHAR (64) UNIQUE NOT NULL, 
            email VARCHAR (120) UNIQUE, password_hash VARCHAR(128) UNIQUE); '''
        self.cursor.execute(user_sql)
        rights_sql = '''
        CREATE TABLE dataset_rights (data_id INT NOT NULL, user_id INT NOT NULL, timestamp timestamp default current_timestamp,
        PRIMARY KEY(data_id, user_id),
        CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(id),
        CONSTRAINT fk_data FOREIGN KEY(data_id) REFERENCES datasets_meta(id))'''
        self.cursor.execute(rights_sql)

        runs_sql = '''
        CREATE TABLE runs (id serial PRIMARY KEY, data_id INT NOT NULL, user_id INT NOT NULL, timestamp timestamp default current_timestamp,
        task_type VARCHAR(256), algo VARCHAR(256) NOT NULL, score FLOAT, target VARCHAR (256), res_table_name VARCHAR (256), 
        CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(id),
        CONSTRAINT fk_data FOREIGN KEY(data_id) REFERENCES datasets_meta(id))
        '''
        self.add_user('datacitizen', 'money100500')
        self.cursor.execute(runs_sql)

    def check_existance_of_dataset(self, dataset_name: str) -> bool:
        query = "select count(*) from datasets_meta where name = %(dataset_name)s"
        data = {'dataset_name': dataset_name}
        self.cursor.execute(query, data)
        count = self.cursor.fetchone()
        return count > 0

    def get_all_datasets_metafeatures(self) -> pd.DataFrame:
        query = "select * from datasets_meta"
        with self.engine.connect() as conn:
            res = conn.execute(query)
            df = pd.DataFrame(res.fetchall())
            df.columns = res.keys()
            return df

    def get_metafeatures_of_datasets(self, ids: List[int]) -> pd.DataFrame:
        query = "SELECT * FROM datasets_meta WHERE id = ANY(%(parameter_array)s)"
        data = {"parameter_array": ids}
        with self.engine.connect() as conn:
            res = conn.execute(query, data)
            df = pd.DataFrame(res.fetchall())
            df.columns = res.keys()
            return df

    def get_user_datasets(self, user_id: int) -> List[int]:
        '''
        Возвращает список из айдишников датасетов, упорядоченных по времени
        :param user_id:
        :return:
        '''
        query = "select data_id from dataset_rights where user_id = %(user_id)s order by timestamp desc"
        data = {'user_id' : user_id}
        self.cursor.execute(query, data)
        res = [x[0] for x in self.cursor.fetchall() if x is not None]
        return res

    def get_last_user_dataset(self, user_id: int) -> int:
        query = "select data_id from dataset_rights where user_id = %(user_id)s order by timestamp desc"
        data = {'user_id': user_id}
        self.cursor.execute(query, data)
        res = self.cursor.fetchone()
        return res[0] if res is not None else None

    def upload_dataset(self, user_id: int, dataset_name: str, data: pd.DataFrame) -> int:
        '''
        :param user_id:
        :param dataset_name:
        :param data:
        :return: айдишник датасета
        '''
        features = {}
        mfe = MFE('all')
        mfe.fit(data._get_numeric_data().values)
        ft = mfe.extract()
        for k, v in zip(ft[0], ft[1]):
            features[k] = v
        table_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        features = {k: v for k, v in features.items() if v is not None and not math.isnan(v)}
        features['name'] = "'" + dataset_name + "'"
        features['data_table'] = "'" + table_name + "'"
        # добавление в таблицу с метаданными
        #features.to_sql('datasets_meta', self.engine, if_exists='append', index=False)
        to_del = []
        for k in features:
            if features[k] == float('inf') or features[k] == float('-inf'):
                to_del.append(k)
        for k in to_del:
            del features[k]
        table_query = ','.join(features.keys())
        table_query = table_query.replace('.', '_')

        vals_query = ','.join([str(x) for x in features.values()])
        metatable_query = f'''
        INSERT INTO datasets_meta({table_query})
        VALUES ({vals_query}) RETURNING id'''
        #alarm!!
        self.cursor.execute(metatable_query)
        id_of_new_row = self.cursor.fetchone()[0]

        # добавление таблицы данных
        data.to_sql(table_name, self.engine, if_exists='replace', index=False)

        query = f'INSERT INTO dataset_rights(data_id, user_id) VALUES({id_of_new_row}, {user_id})'
        self.cursor.execute(query)

        return id_of_new_row


    def get_dataset_data(self, dataset_id) -> pd.DataFrame:
        query = "SELECT data_table FROM datasets_meta WHERE id = %(parameter)s"
        data = {"parameter": dataset_id}
        with self.engine.connect() as conn:
            data_table = conn.execute(query, data).fetchone()[0]
            query = f"SELECT * FROM {data_table}"
            res = conn.execute(query, data)
            df = pd.DataFrame(res.fetchall())
            df.columns = res.keys()
            return df


    def add_user(self, username, password) -> int:
        query = f'''
                INSERT INTO users(username, password_hash)
                VALUES (%(username)s, %(hash)s) RETURNING id'''
        data = {'username': username, 'hash': generate_password_hash(password)}
        self.cursor.execute(query, data)
        res = self.cursor.fetchone()
        return res[0] if res is not None else None


    def tmp_find_user(self, username) -> str:
        query = f"SELECT id FROM users where username='{username}'"
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        if len(res) == 0:
            return None
        return res[0][0]


    def add_run(self, **kwargs) -> int:
        data = kwargs['res_table']
        del kwargs['res_table']
        table_name = 'res_'+''.join(random.choices(string.ascii_lowercase, k=10))
        kwargs['res_table_name'] = table_name
        table_query = ','.join(kwargs.keys())
        for k in kwargs:
            if type(kwargs[k]) == str:
                kwargs[k] = "'" + kwargs[k] + "'"
            else:
                kwargs[k] = str(kwargs[k])
        vals_query = ','.join(kwargs.values())

        run_query = f'''
                INSERT INTO runs({table_query})
                VALUES ({vals_query}) RETURNING id'''
        data.to_sql(table_name, self.engine, if_exists='replace', index=False)
        self.cursor.execute(run_query)
        id_of_new_run = self.cursor.fetchone()[0]
        return id_of_new_run


    def get_user_dataset_runs(self, user_id: int, data_id: int):
        query = "SELECT task_type, algo, target, score FROM runs WHERE user_id = %(user_id)s and data_id = %(data_id)s order by timestamp asc"
        data = {"user_id": user_id, "data_id" : data_id}
        self.cursor.execute(query, data)
        return self.cursor.fetchall()

    def get_run_table_data(self, run_id: int) -> pd.DataFrame:
        query = "SELECT res_table_name FROM runs WHERE id = %(parameter)s"
        data = {"parameter": run_id}
        with self.engine.connect() as conn:
            data_table = conn.execute(query, data).fetchone()[0]
            query = f"SELECT * FROM {data_table}"
            res = conn.execute(query, data)
            df = pd.DataFrame(res.fetchall())
            df.columns = res.keys()
            return df
