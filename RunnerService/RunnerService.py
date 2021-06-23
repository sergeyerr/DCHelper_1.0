from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from typing import Optional, List
from DataServiceAdapter import DataServiceAdapter
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
import sklearn
import catboost
import os

app = FastAPI()
data_service_adapter = DataServiceAdapter(os.getenv('DATA_SERVICE', "localhost:8000"), )


@app.post('/run_classification')
def run_classification_method(user_id: int, data_id: int, method: str, lib: str, target: str):
    data = data_service_adapter.get_dataset_data(data_id)
    data = data._get_numeric_data()
    exec(f'from {lib} import {method}')
    clf = eval(f'{method}()')
    y = data[target]
    X = data.drop([target], axis=1)
    x_train, x_test, y_train, y_test = train_test_split(X, y, train_size=0.9, random_state=42)
    clf.fit(x_train, y_train)
    y_hat = clf.predict(x_test)
    score = f1_score(y_test, y_hat)
    clf.fit(X, y)
    data['res'] = clf.predict(X)
    stream = io.StringIO()
    data.to_csv('tmp.csv', index=False)
    with open('tmp.csv', 'rb') as file:
        return {'run_id' :
                    data_service_adapter.add_run(user_id, data_id, 'classification', method, file, target, score),
                'runs_data': [['classification', method, target, score]]}


@app.post('/run_regression')
def run_regression_method(user_id: int, data_id: int, method: str, lib: str, target: str):
    data = data_service_adapter.get_dataset_data(data_id)
    data = data._get_numeric_data()
    exec(f'from {lib} import {method}')
    clf = eval(f'{method}()')
    scaler = StandardScaler()
    y = scaler.fit_transform(data[target].to_numpy().reshape(-1,1))
    X = data.drop([target], axis=1)
    x_train, x_test, y_train, y_test = train_test_split(X, y, train_size=0.9, random_state=42)
    clf.fit(x_train, y_train)
    y_hat = clf.predict(x_test)
    score = mean_squared_error(y_test.reshape(-1, 1), y_hat.reshape(-1, 1))
    clf.fit(X, y)
    data['res'] = scaler.inverse_transform(clf.predict(X))
    data.to_csv('tmp.csv', index=False)
    with open('tmp.csv', 'rb') as file:
        return {'run_id' :
                    data_service_adapter.add_run(user_id, data_id, 'regression', method, file, target, score),
                'runs_data': [['regression', method, target, score]]}


@app.post('/run_clusterting_method')
def run_clusterting_method(user_id: int, data_id: int, method: str, lib: str):
    data = data_service_adapter.get_dataset_data(data_id)
    data = data._get_numeric_data()
    exec(f'from {lib} import {method}')
    clf = eval(f'{method}()')
    clf.fit(data)
    data['res'] = clf.predict(data)
    stream = io.StringIO()
    data.to_csv('tmp.csv', index=False)
    with open('tmp.csv', 'rb') as file:
        return {'run_id' :
                    data_service_adapter.add_run(user_id, data_id, 'clustering', method, file),
                'runs_data': [['clustering', method, '-', '-']]}
