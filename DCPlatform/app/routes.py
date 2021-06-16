from app import app
from app.utilities import make_branch, find_lib, find_dataset, supervised, is_clustering
from flask import render_template, request, flash, redirect, send_file, url_for
from flask import jsonify, make_response
from werkzeug.utils import secure_filename
from ont_mapping import Ontology, dfs_edges
from app.forms import LoginForm
from flask_login import current_user, login_user
from app.models import User
from flask_login import login_required
from flask_login import logout_user
from werkzeug.urls import url_parse
from app.NLPqueries import QueryProcessor
import pandas as pd
import os
import json
from ActiveHelper import Helper

IA = Helper()
#alarm
#IA.data = pd.read_csv('../crimes.csv')

RES_FOLDER = 'results'
UPLOAD_FOLDER = 'uploads'

ALLOWED_EXTENSIONS = {'ont', 'json'}

files = {}
results = {}
ontologies = {}
query_processors = {}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
@login_required
def index():
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


@app.route('/load_data', methods=['POST'])
@login_required
def load_data():
    file = request.files['file']
    filename = secure_filename(file.filename)
    filename = os.path.join(UPLOAD_FOLDER, current_user.username, filename)
    if not os.path.exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    if not os.path.exists(os.path.join(UPLOAD_FOLDER, current_user.username)):
        os.mkdir(os.path.join(UPLOAD_FOLDER, current_user.username))
    if os.path.exists(filename):
        os.remove(filename)
    file.save(filename)
    files[current_user.username] = filename
    IA.data = pd.read_csv(files[current_user.username])
    return make_response(jsonify({}), 200)


@app.route('/run_method_<methodId>', methods=['GET', 'POST'])
@login_required
def run_by_ontId(methodId):
    ont = ontologies[current_user.username]
    node = ont.__nodes__[methodId]
    dataset = find_dataset(files[current_user.username])
    try:
        data = pd.read_csv(files[current_user.username])
        res = data.copy()

        if supervised(ont, node):
            if dataset:
                target = data[dataset.attributes['<target>']]
            else:
                target = data.target
                data.drop(['target'], axis=1, inplace=True)

        if dataset:
            data = data[dataset.attributes['<used_cols>']]
        else:
            data = data[data.dtypes[data.dtypes != "object"].index]
        name = node.name
    except Exception as e:
        return make_response(jsonify({'exception': str(e)}), 404)
    lib = find_lib(node)
    if not lib:
        return make_response(jsonify({'exception': 'this library is not supported'}), 404)
    lib = lib.name
    if str.find(name, lib) != -1:
        method = name[str.find(name, lib) + len(lib) + 1:]
    else:
        method = name
    exec(f'from {lib} import {method}')
    clf = eval(f'{method}()')
    if supervised(ont, node):
        clf.fit(data, target)
    else:
        clf.fit(data)
    res['predicted'] = clf.predict(data)
    res_dir = os.path.join(RES_FOLDER, current_user.username)
    res_name = method + '.csv'
    if not os.path.exists(RES_FOLDER):
        os.mkdir(RES_FOLDER)
    if not os.path.exists(res_dir):
        os.mkdir(res_dir)
    res.to_csv(os.path.join(res_dir, res_name), index=False, encoding='UTF-8')
    uploads = os.path.join(os.path.dirname(os.getcwd()), 'DCHelper', res_dir, res_name)
    results[current_user.username] = uploads

    if is_clustering(ont, node):
        pie_chart_parts = list(res['predicted'].value_counts())
    else:
        pie_chart_parts = False
    return make_response(jsonify({'pie_chart': pie_chart_parts}), 200)


@app.route('/get_res', methods=['GET', 'POST'])
@login_required
def download_results():
    return send_file(results[current_user.username], as_attachment=True)


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
        user = User.query.filter_by(username=form.username.data).first()
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
    list_of_p = IA.process_query(request.data.decode('utf-8'))
    return json.dumps(list_of_p)

