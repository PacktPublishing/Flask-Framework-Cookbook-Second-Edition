import ldap
from flask import request, render_template, flash, redirect, url_for, \
    session, Blueprint, g
from flask_login import current_user, login_user, logout_user, \
    login_required
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.twitter import make_twitter_blueprint, twitter
from my_app import db, login_manager, get_ldap_connection
from my_app.auth.models import User, RegistrationForm, LoginForm


auth = Blueprint('auth', __name__)
facebook_blueprint = make_facebook_blueprint(
    scope='email', redirect_to='auth.facebook_login')
google_blueprint = make_google_blueprint(
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"],
    redirect_to='auth.google_login')
twitter_blueprint = make_twitter_blueprint(redirect_to='auth.twitter_login')


@auth.route("/ldap-login", methods=['GET', 'POST'])
def ldap_login():
    if current_user.is_authenticated:
        flash('Your are already logged in.', 'info')
        return redirect(url_for('auth.home'))

    form = LoginForm()

    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            conn = get_ldap_connection()
            conn.simple_bind_s(
                'cn=%s,dc=example,dc=org' % username,
                password
            )
        except ldap.INVALID_CREDENTIALS:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html', form=form)

        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username, password)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        flash('You have successfully logged in.', 'success')
        return redirect(url_for('auth.home'))

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('login.html', form=form)


@auth.route("/facebook-login")
def facebook_login():
    if not facebook.authorized:
        return redirect(url_for("facebook.login"))

    resp = facebook.get("/me?fields=name,email")

    user = User.query.filter_by(username=resp.json()["email"]).first()
    if not user:
        user = User(resp.json()["email"], '')
        db.session.add(user)
        db.session.commit()

    login_user(user)
    flash(
        'Logged in as name=%s using Facebook login' % (
            resp.json()['name']), 'success' )
    return redirect(request.args.get('next', url_for('auth.home')))


@auth.route("/google-login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v1/userinfo")

    user = User.query.filter_by(username=resp.json()["email"]).first()
    if not user:
        user = User(resp.json()["email"], '')
        db.session.add(user)
        db.session.commit()

    login_user(user)
    flash(
        'Logged in as name=%s using Google login' % (
            resp.json()['name']), 'success' )
    return redirect(request.args.get('next', url_for('auth.home')))


@auth.route("/twitter-login")
def twitter_login():
    if not twitter.authorized:
        return redirect(url_for("twitter.login"))

    resp = twitter.get("account/verify_credentials.json")

    user = User.query.filter_by(username=resp.json()["screen_name"]).first()
    if not user:
        user = User(resp.json()["screen_name"], '')
        db.session.add(user)
        db.session.commit()

    login_user(user)
    flash(
        'Logged in as name=%s using Twitter login' % (
            resp.json()['name']), 'success' )
    return redirect(request.args.get('next', url_for('auth.home')))


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
