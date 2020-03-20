from flask import render_template
from flask import Flask
from flask import redirect
from flask import url_for

# import logging

from src import Forms

from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my temp secret key'

PORT, HOST = 8080, "127.0.0.1"
DEBUG = True


@app.route('/')
@app.route('/index')
def index():
    title = 'debug'
    return render_template('base.html', title=title)


@app.route('/login', methods=['GET', 'POST'])
def login():
    title = 'Login or sign in'
    form = Forms.LoginForm()

    if form.validate_on_submit():
        return redirect('/index')

    return render_template('login.html', title=title, form=form)


if __name__ == '__main__':
#    logging.info('Init database session')
#   db_session.global_init("db/bugtracker.sqlite")

    # logging.info(f'Running app on {HOST}:{PORT}, DEBUG_MODE: {DEBUG}')
    app.run(port=PORT, host=HOST, debug=DEBUG)
