from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)
api = Api(app)

app.secret_key = 'some_random_key'

from my_app.catalog.views import catalog
app.register_blueprint(catalog)

db.create_all()
