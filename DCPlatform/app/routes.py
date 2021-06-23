from app import app
from app.utilities import *
from app import data_service_adapter, runner_service_adapter
from flask import render_template, request, flash, redirect, send_file, url_for
from flask import jsonify, make_response
from werkzeug.utils import secure_filename
from ont_mapping import Ontology, dfs_edges
from app.forms import LoginForm
from flask_login import current_user, login_user
from app.models import Users
from flask_login import login_required
from flask_login import logout_user
from werkzeug.urls import url_parse
from app.NLPqueries import QueryProcessor

import pandas as pd
import os
import json
from ActiveHelper import Helper

#alarm
#IA.data = pd.read_csv('../crimes.csv')

RES_FOLDER = 'results'
UPLOAD_FOLDER = 'uploads'

ALLOWED_EXTENSIONS = {'ont', 'json'}

current_data_ids = {}
current_targets = {}
results = {}
ontologies = {}
query_processors = {}
active_assistants = {}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
@login_required
def index():
    prev_datasets = data_service_adapter.get_user_datasets(user_name=current_user.username)
    if len(prev_datasets) > 0:
        return render_template('index.html', prev_datasets=prev_datasets)
    return render_template('index.html')


@app.route('/tree', methods=['POST'])
@login_required
def make_tree():
    ont_str = request.form['ont']
    ont = Ontology(json_string=ont_str)
    query_processors[current_user.username] = QueryProcessor(ont)
    ontologies[current_user.username] = ont
    init_node = ont.select_nodes('node.name == "init"')[0]
    tree_roots_edges = dfs_edges(init_node, passing_out=[''])
    res = []
    for edge in tree_roots_edges:
        root = edge.dest
        res.append(make_branch(ont, node=root, input_edges_dfs=root.attributes['<descend_in_edges>']))
    return jsonify(res)

@app.route('/select_old_data_<dataId>', methods=['POST'])
@login_required
def select_old_data(dataId :int):
    active_assistants[current_user.username].data = data_service_adapter.get_dataset_data(dataId)
    active_assistants[current_user.username].data_id = dataId
    current_data_ids[current_user.username] = dataId
    return make_response(jsonify({}), 200)

@app.route('/load_data', methods=['POST'])
@login_required
def load_data():
    file = request.files['file']
    filename = secure_filename(file.filename)
   # filename = os.path.join(UPLOAD_FOLDER, current_user.username, filename)
    # if not os.path.exists(UPLOAD_FOLDER):
    #     os.mkdir(UPLOAD_FOLDER)
    # if not os.path.exists(os.path.join(UPLOAD_FOLDER, current_user.username)):
    #     os.mkdir(os.path.join(UPLOAD_FOLDER, current_user.username))
    # if os.path.exists(filename):
    #     os.remove(filename)
    # #file.save(filename)
    #files[current_user.username] = filename
    data_id = data_service_adapter.upload_dataset(filename, file, user_name=current_user.username)
    active_assistants[current_user.username].data = data_service_adapter.get_dataset_data(data_id)
    active_assistants[current_user.username].data_id = data_id
    current_data_ids[current_user.username] = data_id
    if current_user.username in current_targets:
        del current_targets[current_user.username]
    #IA.data = pd.read_csv(files[current_user.username])

    return make_response(jsonify({}), 200)


@app.route('/run_method_<methodId>', methods=['GET', 'POST'])
@login_required
def run_by_ontId(methodId):
    ont = ontologies[current_user.username]
    node = ont.__nodes__[methodId]
    data_id = current_data_ids[current_user.username]
    user_id = data_service_adapter.get_user_id(current_user.username)
    if active_assistants[current_user.username].target_col:
        target = active_assistants[current_user.username].target_col
    else:
        target = 'target'
    lib = find_lib(node)
    if not lib:
        return make_response(jsonify({'exception': 'this library is not supported'}), 404)
    lib = lib.name
    name = node.name
    if str.find(name, lib) != -1:
        method = name[str.find(name, lib) + len(lib) + 1:]
    else:
        method = name
    if is_regression(ont, node) and is_classification(ont, node):
        if 'class' in method.lower():
            results[current_user.username] = runner_service_adapter.run_classification_method(user_id, data_id, method,
                                                                                              lib, target)
        else:
            results[current_user.username] = runner_service_adapter.run_classification_method(user_id, data_id, method,
                                                                                              lib, target)

    elif is_regression(ont, node):
        results[current_user.username] = runner_service_adapter.run_regression_method(user_id, data_id, method, lib, target)
    elif is_classification(ont, node):
        results[current_user.username] = runner_service_adapter.run_classification_method(user_id, data_id, method, lib, target)
    elif is_clustering(ont, node):
        results[current_user.username] = runner_service_adapter.run_clusterting_method(user_id, data_id, method, lib)
    else:
        return make_response(jsonify({'exception': 'such task is not supported'}), 404)
        #raise Exception('such task is not supported')
    return make_response(jsonify({'pie_chart': False}), 200)


@app.route('/get_res', methods=['GET', 'POST'])
@login_required
def download_results():
    df = data_service_adapter.get_run_data(results[current_user.username])
    df.to_csv('./app/res.csv', index=False)
    return send_file('./res.csv', as_attachment=True)


@app.route('/nlp_query', methods=['GET', 'POST'])
@login_required
def process_query():
    if current_user.username not in query_processors:
        return make_response(jsonify({}), 404)
    query = request.values['query']
    answer = query_processors[current_user.username].process_query(query)
    answer = [{"id": x[0], "text": x[1]} for x in answer]
    answer = {'results': answer}
    return make_response(jsonify(answer), 200)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Вход', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/bot', methods=['POST'])
@login_required
def bot_answer():
    if current_user.username not in active_assistants:
        active_assistants[current_user.username] = Helper()
    list_of_p = active_assistants[current_user.username].process_query(request.data.decode('utf-8'))
    return json.dumps(list_of_p)

