from flask import Flask
from flask_bootstrap import Bootstrap
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from ont_mapping import ontology
from DataServiceAdapter import DataServiceAdapter
from RunnerServiceAdapter import RunnerServiceAdapter
import os
from flask_bootstrap import WebCDN, StaticCDN

app = Flask(__name__)
app.config.from_object(Config)
bootstrap = Bootstrap(app)
#app.extensions['bootstrap']['cdns']['jquery'] = StaticCDN
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
data_service_adapter = DataServiceAdapter(os.getenv('DATA_SERVICE', "localhost:8000"))
runner_service_adapter = RunnerServiceAdapter(os.getenv('RUNNER_SERVICE', "localhost:8081"))


from app import routes, models
