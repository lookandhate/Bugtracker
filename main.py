from flask import render_template
from flask import Flask
from flask import redirect
from flask import url_for

from flask_login import LoginManager
from flask_login import login_user, login_required, logout_user

# import logging
from data.users import User
from src import Forms

from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my temp secret key'

login_manager = LoginManager()
login_manager.init_app(app)

PORT, HOST = 8080, "127.0.0.1"
DEBUG = True


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    title = 'debug'
    return render_template('base.html', title=title)


@app.route('/login', methods=['GET', 'POST'])
def login():
    title = 'Login'
    form = Forms.LoginForm()

    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/join', methods=['GET', 'POST'])
def join():
    title = 'Join us'
    form = Forms.RegistrationForm()

    if form.validate_on_submit():
        return redirect('/index')

    return render_template('login.html', title=title, form=form)


if __name__ == '__main__':
    #    logging.info('Init database session')
    #   db_session.global_init("db/bugtracker.sqlite")

    # logging.info(f'Running app on {HOST}:{PORT}, DEBUG_MODE: {DEBUG}')
    app.run(port=PORT, host=HOST, debug=DEBUG)
