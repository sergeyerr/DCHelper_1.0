from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from PostgresWorker.PostgresWorker import PostgresWorker as PostgresAdapter
from typing import Optional, List
import os

user = os.getenv('PG_USERNAME', "postgres")
password = os.getenv('PG_PASS', "postgres")
db_name = os.getenv('PG_DB', "test")
host = os.getenv('PG_HOST', "localhost")

if os.path.exists('./db_inited'):
    db_adapter = PostgresAdapter(user, password, db_name, host)
else:
    os.mkdir('./db_inited')
    print('initin db')
    db_adapter = PostgresAdapter(user, password, db_name, host, True)
app = FastAPI()


@app.post('/tmp_insert_user/{username}')
def insert_user(username: str):
    return {"user_id": db_adapter.tmp_add_user(username)}


@app.post("/upload_csv/")
def upload_csv(dataset_name: str, csv_file: bytes = File(...), user_id: Optional[int] = None,
               user_name: Optional[str] = None):
    if not user_id:
        if not user_name:
            raise HTTPException(status_code=404, detail="No username or ID")
        user_id = db_adapter.tmp_find_user(user_name)
    dataframe = pd.read_csv(io.BytesIO(csv_file))

    # do something with dataframe here (?)
    return {"dataset_id": db_adapter.upload_dataset(user_id, dataset_name, dataframe)}


@app.get("/get_user_datasets")
def get_user_datasets(user_id: Optional[int] = None, user_name: Optional[str] = None):
    if not user_id:
        if not user_name:
            raise HTTPException(status_code=404, detail="No username or ID")
        user_id = db_adapter.tmp_find_user(user_name)
    ids = db_adapter.get_user_datasets(user_id)
    names = []
    for id in ids:
        names.append(db_adapter.get_metafeatures_of_datasets([id])['name'][0])
    return {'dataset_ids': ids,
            'names': names}


@app.get("/get_last_user_dataset")
def get_last_user_dataset(user_id: Optional[int] = None, user_name: Optional[str] = None):
    if not user_id:
        if not user_name:
            raise HTTPException(status_code=404, detail="No username or ID")
        user_id = db_adapter.tmp_find_user(user_name)
    id = db_adapter.get_last_user_dataset(user_id)
    return {'dataset_id': db_adapter.get_last_user_dataset(user_id),
            'name': db_adapter.get_metafeatures_of_datasets([id])['name'][0] if id is not None else None}


@app.get("/get_dataset_data")
def get_dataset_data(dataset_id: int):
    df = db_adapter.get_dataset_data(dataset_id)

    stream = io.StringIO()

    df.to_csv(stream, index=False)

    response = StreamingResponse(iter([stream.getvalue()]),
                                 media_type="text/csv"
                                 )

    response.headers["Content-Disposition"] = "attachment; filename=export.csv"

    return response


@app.get("/get_metafeatures_of_datasets")
def get_metafeatures_of_datasets(ids: List[int] = Query(None)):
    df = db_adapter.get_metafeatures_of_datasets(ids)

    stream = io.StringIO()

    df.to_csv(stream, index=False)

    response = StreamingResponse(iter([stream.getvalue()]),
                                 media_type="text/csv"
                                 )

    response.headers["Content-Disposition"] = "attachment; filename=export.csv"

    return response


@app.get("/get_all_metafeatures")
def get_all_metafeatures():
    df = db_adapter.get_all_datasets_metafeatures()

    stream = io.StringIO()

    df.to_csv(stream, index=False)

    response = StreamingResponse(iter([stream.getvalue()]),
                                 media_type="text/csv"
                                 )

    response.headers["Content-Disposition"] = "attachment; filename=export.csv"

    return response


@app.post('/add_run')
def add_run(user_id: int, data_id: int, task_type: str, algo: str,
            target: Optional[str] = None, score: Optional[float] = None, res_table: bytes = File(...)):
    dataframe = pd.read_csv(io.BytesIO(res_table))
    kwargs = {'user_id': user_id,
              'data_id': data_id,
              'task_type': task_type,
              'algo': algo,
              'res_table': dataframe,
              }
    if target:
        kwargs['target'] = target
    if score:
        kwargs['score'] = score
    return {'run_id': db_adapter.add_run(**kwargs)}


@app.get('/get_user_dataset_runs')
def get_user_dataset_runs(user_id: int, data_id: int):
    return {'runs_data': db_adapter.get_user_dataset_runs(user_id, data_id)}


@app.get("/get_run_data")
def get_run_data(run_id: int):
    df = db_adapter.get_run_table_data(run_id)

    stream = io.StringIO()

    df.to_csv(stream, index=False)

    response = StreamingResponse(iter([stream.getvalue()]),
                                 media_type="text/csv"
                                 )

    response.headers["Content-Disposition"] = "attachment; filename=export.csv"

    return response


@app.get("/get_user_id")
def get_user_id(username: str):
    return {'user_id': db_adapter.tmp_find_user(username)}
