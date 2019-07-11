from functools import wraps
from flask import request, render_template, flash, redirect, url_for, \
    session, Blueprint, g, abort
from flask_login import current_user, login_user, logout_user, \
    login_required
from wtforms import PasswordField
from my_app import db, login_manager
from flask_admin import BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from flask_admin.actions import ActionsMixin
from my_app.auth.models import User, RegistrationForm, LoginForm, \
    AdminUserCreateForm, AdminUserUpdateForm, generate_password_hash, \
    CKTextAreaField

auth = Blueprint('auth', __name__)


def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            return abort(403)
        return func(*args, **kwargs)
    return decorated_view


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@auth.before_request
def get_current_user():
    g.user = current_user


@auth.route('/')
@auth.route('/home')
def home():
    return render_template('home.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('Your are already logged in.', 'info')
        return redirect(url_for('auth.home'))

    form = RegistrationForm()

    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash(
                'This username has been already taken. Try another one.',
                'warning'
            )
            return render_template('register.html', form=form)
        user = User(username, password)
        db.session.add(user)
        db.session.commit()
        flash('You are now registered. Please login.', 'success')
        return redirect(url_for('auth.login'))

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('auth.home'))

    form = LoginForm()

    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = User.query.filter_by(username=username).first()

        if not (existing_user and existing_user.check_password(password)):
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html', form=form)

        login_user(existing_user)
        flash('You have successfully logged in.', 'success')
        return redirect(url_for('auth.home'))

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.home'))


@auth.route('/admin')
@login_required
@admin_login_required
def home_admin():
    return render_template('admin-home.html')


@auth.route('/admin/users-list')
@login_required
@admin_login_required
def users_list_admin():
    users = User.query.all()
    return render_template('users-list-admin.html', users=users)


@auth.route('/admin/create-user', methods=['GET', 'POST'])
@login_required
@admin_login_required
def user_create_admin():
    form = AdminUserCreateForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        admin = form.admin.data
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash(
                'This username has been already taken. Try another one.',
                'warning'
            )
            return render_template('register.html', form=form)
        user = User(username, password, admin)
        db.session.add(user)
        db.session.commit()
        flash('New User Created.', 'info')
        return redirect(url_for('auth.users_list_admin'))

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('user-create-admin.html', form=form)


@auth.route('/admin/update-user/<id>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def user_update_admin(id):
    user = User.query.get(id)
    form = AdminUserUpdateForm(
        username=user.username,
        admin=user.admin
    )

    if form.validate_on_submit():
        username = form.username.data
        admin = form.admin.data

        User.query.filter_by(id=id).update({
            'username': username,
            'admin': admin,
        })

        db.session.commit()
        flash('User Updated.', 'info')
        return redirect(url_for('auth.users_list_admin'))

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('user-update-admin.html', form=form, user=user)


@auth.route('/admin/delete-user/<id>')
@login_required
@admin_login_required
def user_delete_admin(id):
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    flash('User Deleted.', 'info')
    return redirect(url_for('auth.users_list_admin'))


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()


class UserAdminView(ModelView, ActionsMixin):
    column_searchable_list = ('username',)
    column_sortable_list = ('username', 'admin')
    column_exclude_list = ('pwdhash',)
    form_excluded_columns = ('pwdhash',)
    form_edit_rules = (
        'username', 'admin', 'roles', 'notes',
        rules.Header('Reset Password'),
        'new_password', 'confirm'
    )
    form_create_rules = (
        'username', 'admin', 'roles', 'notes', 'password'
    )
    form_overrides = dict(notes=CKTextAreaField)

    create_template = 'edit.html'
    edit_template = 'edit.html'

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

    def scaffold_form(self):
        form_class = super(UserAdminView, self).scaffold_form()
        form_class.password = PasswordField('Password')
        form_class.new_password = PasswordField('New Password')
        form_class.confirm = PasswordField('Confirm New Password')
        return form_class

    def create_model(self, form):
        if 'C' not in current_user.roles:
            flash('You are not allowed to create users.', 'warning')
            return
        model = self.model(
            form.username.data, form.password.data, form.admin.data,
            form.notes.data
        )
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()

    def update_model(self, form, model):
        if 'U' not in current_user.roles:
            flash('You are not allowed to edit users.', 'warning')
            return
        form.populate_obj(model)
        if form.new_password.data:
            if form.new_password.data != form.confirm.data:
                flash('Passwords must match')
                return
            model.pwdhash = generate_password_hash(form.new_password.data)
        self.session.add(model)
        self._on_model_change(form, model, False)
        self.session.commit()

    def delete_model(self, model):
        if 'D' not in current_user.roles:
            flash('You are not allowed to delete users.', 'warning')
            return
        super(UserAdminView, self).delete_model(model)

    def is_action_allowed(self, name):
        if name == 'delete' and 'D' not in current_user.roles:
            flash('You are not allowed to delete users.', 'warning')
            return False
        return True
