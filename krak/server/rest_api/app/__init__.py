import pathlib
import os

import connexion
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

base_dir = pathlib.Path(__file__).parent

connex_app = connexion.App(__name__, specification_dir=base_dir.as_posix())
app = connex_app.app

try:
    db_user = os.environ['POSTGRES_USER']
    db_password = os.environ['POSTGRES_PASSWORD']
    db_port = os.environ['POSTGRES_PORT']
    db_name = os.environ['POSTGRES_DB']
    db_host = os.environ['POSTGRES_HOST']
    db_uri = (
        f'postgres+psycopg2://'
        f'{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
except KeyError:
    app.logger.warn(
        'PostgreSQL credentials not found in ENV - setting backend as sqlite')
    db_uri = 'sqlite://'

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

sql = SQLAlchemy(app)

ma = Marshmallow(app)
