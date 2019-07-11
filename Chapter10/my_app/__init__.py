import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

ALLOWED_LANGUAGES = {
    'en': 'English',
    'fr': 'French',
}

RECEPIENTS = ['some_receiver@gmail.com']

sentry_sdk.init(
    dsn="https://1234:5678@fake-sentry-server/1",
    integrations=[FlaskIntegration()]
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.realpath('.') + '/my_app/static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['WTF_CSRF_SECRET_KEY'] = 'random key for form'
db = SQLAlchemy(app)

app.config['LOG_FILE'] = 'application.log'


if not app.debug:
    import logging
    logging.basicConfig(level=logging.INFO)
    from logging import FileHandler, Formatter
    from logging.handlers import SMTPHandler
    file_handler = FileHandler(app.config['LOG_FILE'])
    app.logger.addHandler(file_handler)
    mail_handler = SMTPHandler(
        ("smtp.gmail.com", 587), 'sender@gmail.com', RECEPIENTS,
        'Error occurred in your application',
        ('some_email@gmail.com', 'some_gmail_password'), secure=())
    mail_handler.setLevel(logging.ERROR)
    # app.logger.addHandler(mail_handler)
    for handler in [file_handler, mail_handler]:
        handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))


babel = Babel(app)

app.secret_key = 'some_random_key'

from my_app.catalog.views import catalog
app.register_blueprint(catalog)

db.create_all()
