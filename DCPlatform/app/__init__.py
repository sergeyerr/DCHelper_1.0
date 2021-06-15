from flask import Flask
from flask_bootstrap import Bootstrap
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from ont_mapping import ontology
from flask_bootstrap import WebCDN, StaticCDN

app = Flask(__name__)
app.config.from_object(Config)
bootstrap = Bootstrap(app)
#app.extensions['bootstrap']['cdns']['jquery'] = StaticCDN
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
try:
    datasets_ont = ontology.Ontology(file=app.config['DATASETS_ONT'])
except Exception:
    datasets_ont = None


from app import routes, models
