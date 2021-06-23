import httpx
from typing import BinaryIO, List
import pandas as pd
from io import StringIO

class RunnerServiceAdapter:
    def __init__(self, service_adress):
        self.address = service_adress
        
    def run_classification_method(self, user_id: int, data_id: int, method: str, lib: str, target: str):
        params = [('user_id', user_id),
              ('data_id', data_id),
              ('method', method),
              ('lib', lib),
              ('target', target)
              ]
        try:
            r = httpx.post(f"http://{self.address}/run_classification",params = params, timeout=60)
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return r.json()['run_id'], r.json()['runs_data']
    
    def run_regression_method(self, user_id: int, data_id: int, method: str, lib: str, target: str):
        params = [('user_id', user_id),
              ('data_id', data_id),
              ('method', method),
              ('lib', lib),
              ('target', target)
              ]
        try:
            r = httpx.post(f"http://{self.address}/run_regression",params = params)
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return r.json()['run_id'], r.json['runs_data']
        
    def run_clusterting_method(self, user_id: int, data_id: int, method: str, lib: str):
        params = [('user_id', user_id),
              ('data_id', data_id),
              ('method', method),
              ('lib', lib)
              ]
        try:
            r = httpx.post(f"http://{self.address}/run_clusterting_method",params = params)
        except httpx.HTTPError as exc:
            print(f"An error {exc.response.status_code} occurred while requesting {exc.request.url!r}.")
            return None
        return r.json()['run_id'], r.json['runs_data']