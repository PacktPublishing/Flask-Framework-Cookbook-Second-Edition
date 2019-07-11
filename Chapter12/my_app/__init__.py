from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from elasticsearch import Elasticsearch
from flask_caching import Cache
from flask_mail import Mail
from celery import Celery



app = Flask(__name__)
app.config['SERVER_NAME'] = 'localhost:5000'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['WHOOSH_BASE'] = '/tmp/whoosh'
db = SQLAlchemy(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'gmail_username'
app.config['MAIL_PASSWORD'] = 'gmail_password'
app.config['MAIL_DEFAULT_SENDER'] = ('Sender name', 'sender email')
mail = Mail(app)

app.secret_key = 'some_random_key'

es = Elasticsearch('http://localhost:9200/')
es.indices.create('catalog', ignore=400)

app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)

def make_celery(app):
    celery = Celery(
        app.import_name, broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

from my_app.catalog.views import catalog
app.register_blueprint(catalog)

db.create_all()
