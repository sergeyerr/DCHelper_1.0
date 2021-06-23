import os
basedir = os.path.abspath(os.path.dirname(__file__))

user = os.getenv('PG_USERNAME', "postgres")
password = os.getenv('PG_PASS', "postgres")
db_name = os.getenv('PG_DB', "test")
host = os.getenv('PG_HOST', "localhost")

class Config(object):
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #                           'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              f'postgresql+psycopg2://{user}:{password}@{host}/{db_name}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
