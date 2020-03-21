import os
import hashlib

from flask import render_template, send_from_directory
from flask import Flask
from flask import redirect
from flask import url_for

from flask_login import LoginManager
from flask_login import login_user, login_required, logout_user, current_user

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
    result = session.query(User).get(user_id)
    session.close()
    return result


# Main page of app
@app.route('/')
@app.route('/index')
def index():
    session = db_session.create_session()
    registered_users = len(session.query(User).all())
    title = 'debug'
    session.close()
    return render_template('base.html', title=title, registred_users=registered_users)


# Registration page
@app.route('/join', methods=['GET', 'POST'])
def join():
    title = 'Join us'

    session = db_session.create_session()
    registred_users = len(session.query(User).all())

    # Registration form
    form = Forms.RegistrationForm()

    # And finally, redirecting to index page
    if form.validate_on_submit():
        # Creating Database Session
        session = db_session.create_session()

        # checking if user already registered
        if session.query(User).filter(User.username == form.username.data).all():
            session.close()
            return render_template('join.html',
                                   message="User already registered",
                                   form=form)

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

        session.close()
        return redirect('/index')
    session.close()
    return render_template('join.html', title=title, form=form, registred_users=registred_users)


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    title = 'Login'
    form = Forms.LoginForm()

    session = db_session.create_session()
    registred_users = len(session.query(User).all())

    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.username == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            print(current_user)

            session.close()
            return redirect("/")

        session.close()
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    session.close()
    return render_template('login.html', title=title, form=form, registred_users=registred_users)


# Logout page
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/profile/<user_id>')
@login_required
def profile(user_id):
    session = db_session.create_session()
    registered_users = len(session.query(User).all())

    # Get data that we need
    username = session.query(User.username).filter(User.id == user_id).first()[0]
    projects = session.query(User.projects).filter(User.id == user_id).first()[0]
    role = session.query(User.role).filter(User.id == user_id).first()[0]
    date_of_reg = session.query(User.created_date).filter(User.id == user_id).first()[0]

    # Unpacking datetime.datetime object on time units
    date_of_reg = f'{date_of_reg.day}-{date_of_reg.month}-{date_of_reg.year} at {date_of_reg.hour}:{date_of_reg.minute}:{date_of_reg.second}'

    session.close()

    return render_template('profile.html', title=f'{username}', id=user_id, username=username, projects=projects,
                           role=role,
                           date_of_reg=date_of_reg, registred_users=registered_users)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    #    logging.info('Init database session')
    db_session.global_init("db/bugtracker.sqlite")

    # logging.info(f'Running app on {HOST}:{PORT}, DEBUG_MODE: {DEBUG}')
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=1)
