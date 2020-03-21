import os
import hashlib

from flask import render_template, send_from_directory
from flask import Flask
from flask import redirect
from flask import url_for

from flask_login import LoginManager
from flask_login import login_user, login_required, logout_user

# import logging
from data.users import User
from src import Forms

from data import db_session

# Init flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'my temp secret key'

# Init login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Port, IP address and debug mode
PORT, HOST = 8080, "127.0.0.1"
DEBUG = True


# Loading current user
@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


# Main page of app
@app.route('/')
@app.route('/index')
def index():
    title = 'debug'
    return render_template('base.html', title=title)


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    title = 'Login'
    form = Forms.LoginForm()

    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.username == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title=title, form=form)


# Logout page
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# Registration page
@app.route('/join', methods=['GET', 'POST'])
def join():
    title = 'Join us'

    # Registration form
    form = Forms.RegistrationForm()

    # And finally, redirecting to index page
    if form.validate_on_submit():
        # Creating Database Session
        session = db_session.create_session()

        # User object for database
        user = User()

        # Hashing password here
        password_hash = hashlib.new('md5', bytes(form.password.data, encoding='utf8'))

        # Filling database with user data
        user.username = form.username.data

        # Here we use not password but its hash
        user.hashed_password = password_hash.hexdigest()

        # Adding user to database
        session.merge(user)
        # Commiting changes
        session.commit()

        return redirect('/index')

    return render_template('join.html', title=title, form=form)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    #    logging.info('Init database session')
    db_session.global_init("db/bugtracker.sqlite")

    # logging.info(f'Running app on {HOST}:{PORT}, DEBUG_MODE: {DEBUG}')
    app.run(port=PORT, host=HOST, debug=DEBUG)
