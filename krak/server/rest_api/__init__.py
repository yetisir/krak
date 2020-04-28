import pathlib

import connexion
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

base_dir = pathlib.Path(__file__).parent

app = connexion.App(__name__, specification_dir=base_dir.as_posix()).app

app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgres://admin:admin@10.0.0.223:5423/borehole_database')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

sql = SQLAlchemy(app)

ma = Marshmallow(app)
