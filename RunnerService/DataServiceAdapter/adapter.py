import httpx
from typing import BinaryIO, List
import pandas as pd
from io import StringIO


class DataServiceAdapter:
    def __init__(self, service_adress):
        self.address = service_adress

    def upload_dataset(self, dataset_name: str,csv_file_stream : BinaryIO, user_name = None, user_id = None) -> int:
        '''
        необязательно указывать user_name и user_id, можно только одно
        '''
        params = [('dataset_name', dataset_name)]
        if user_name:
            params.append(('user_name', user_name))
        if user_id:
            params.append(('user_id', user_id))
        files = {
        'csv_file': csv_file_stream
        }
        try:
            r = httpx.post(f"http://{self.address}/upload_csv",params = params, files=files)
            r.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return r.json()['dataset_id']


    def get_dataset_data(self, dataset_id: int) -> pd.DataFrame:
        params = [('dataset_id', dataset_id)]
        try:
            r = httpx.get(f"http://{self.address}/get_dataset_data",params = params)
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return pd.read_csv(StringIO(r.read().decode('utf-8')))


    def get_user_datasets(self,  user_name : str = None, user_id : str = None) -> List[int]:
        params = []
        if user_name:
            params.append(('user_name', user_name))
        if user_id:
            params.append(('user_id', user_id))
        try:
            r = httpx.get(f"http://{self.address}/get_user_datasets",params = params)
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return list(zip(r.json()['dataset_ids'], r.json()['names']))


    def get_last_user_dataset(self,  user_name : str = None, user_id : str = None) -> List[int]:
        params = []
        if user_name:
            params.append(('user_name', user_name))
        if user_id:
            params.append(('user_id', user_id))
        try:
            r = httpx.get(f"http://{self.address}/get_last_user_dataset",params = params)
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return r.json()['dataset_id'], r.json()['name']


    def get_metafeatures_of_datasets(self,  datasets_ids : List[int]) -> pd.DataFrame:
        params = {'ids' : dataset_ids}
        try:
            r = httpx.get(f"http://{self.address}/get_metafeatures_of_datasets",params = params)
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return pd.read_csv(StringIO(r.read().decode('utf-8')))


    def get_all_metafeatures(self) -> pd.DataFrame:
        try:
            r = httpx.get(f"http://{self.address}/get_all_metafeatures")
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return pd.read_csv(StringIO(r.read().decode('utf-8')))
    
    
    def get_all_metafeatures(self) -> pd.DataFrame:
        try:
            r = httpx.get(f"http://{self.address}/get_all_metafeatures")
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return pd.read_csv(StringIO(r.read().decode('utf-8')))
    
    def add_run(self, user_id: int, data_id: int, task_type: str, algo: str, res_table_stream: BinaryIO,
            target: str = None, score: float = None):
        params = [('user_id', user_id),
              ('data_id', data_id),
              ('task_type', task_type),
              ('algo', algo)
              ]
        if target:
            params.append(('target', target))
        if score:
             params.append(('score', score))
            
        files = {
        'res_table':  res_table_stream
        }
        
        try:
            r = httpx.post(f"http://{self.address}/add_run",params = params, files=files)
            r.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return r.json()['run_id']
    
    
    def get_run_data(self, run_id: int):
        params = [('run_id', run_id)]
        try:
            r = httpx.get(f"http://{self.address}/get_run_data",params = params)
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return pd.read_csv(StringIO(r.read().decode('utf-8')))
        
        
    def get_user_id(self, username: str):
        params = [('username', username)]
        try:
            r = httpx.get(f"http://{self.address}/get_user_id",params = params)
            r.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return r.json()['user_id']