from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['WTF_CSRF_SECRET_KEY'] = 'random key for form'
db = SQLAlchemy(app)

app.secret_key = 'some_random_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

import my_app.auth.views as views
admin = Admin(app, index_view=views.MyAdminIndexView())
admin.add_view(views.UserAdminView(views.User, db.session))

from my_app.auth.views import auth
app.register_blueprint(auth)

db.create_all()
