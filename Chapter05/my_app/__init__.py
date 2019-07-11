import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.realpath('.') + '/my_app/static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['WTF_CSRF_SECRET_KEY'] = 'random key for form'
db = SQLAlchemy(app)

app.secret_key = 'some_random_key'

from my_app.catalog.views import catalog
app.register_blueprint(catalog)

db.create_all()
