import os
import hashlib

from data.models import association_table_user_to_project

from sqlalchemy import update, delete

from flask import render_template, send_from_directory, flash, url_for, redirect
from flask import Flask

from flask_login import LoginManager
from flask_login import login_user, login_required, logout_user, current_user

# import logging
from data.models import User, Project, Issue
from data import db_session

from src import Forms

# Init flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'my temp secret key'

# Init login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Port, IP address and debug mode
PORT, HOST = 8080, "127.0.0.1"
DEBUG = True


# Some debug info for me
def debug_info():
    session = db_session.create_session()
    registered_users = len(session.query(User).all())


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
    registered_users = len(session.query(User).all())

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

        flash('Your account has been created and now you are able to log in', 'success')
        return redirect('/index')
    session.close()
    return render_template('join.html', title=title, form=form, registred_users=registered_users)


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
            session.close()

        else:
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
    user = session.query(User).filter(User.id == user_id).first()

    # Checking is user exist
    if user is not None:
        return render_template('profile.html', title=f'{user.username}', id=user_id, user=user,
                               registred_users=registered_users)

    # If user doesn't exist, throw error page
    return render_template('error.html', error_code=404, error_message='User has been deleted or wasn`t registered',
                           registred_users=registered_users)


@app.route('/profile/<user_id>/projects')
@login_required
def profile_projects(user_id):
    session = db_session.create_session()
    registered_users = len(session.query(User).all())

    pass


@app.route('/profile/<user_id>/issues')
@login_required
def profile_issues(user_id):
    # TODO: Implement user Issues
    pass


@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    title = 'Create project'
    creating_project_form = Forms.CreateProject()
    session = db_session.create_session()
    registered_users = len(session.query(User).all())

    if creating_project_form.validate_on_submit():
        if session.query(Project).filter(Project.project_name == creating_project_form.project_name.data).all():
            session.close()
            return render_template('index.html',
                                   message="Project with that name already created",
                                   form=creating_project_form)

        project = Project(project_name=creating_project_form.project_name.data)

        project.members.append(current_user)

        # Commiting changes
        session.merge(project)
        session.commit()
        session.close()

        # Re-creating session to update DB state
        session = db_session.create_session()
        project_id = \
            session.query(Project.id).filter(Project.project_name == creating_project_form.project_name.data).first()[0]

        # Updating association table with new user role
        upd = association_table_user_to_project.update().values(project_role='root').where(
            association_table_user_to_project.c.member_id == current_user.id).where(
            association_table_user_to_project.c.project_id == project_id)
        session.execute(upd)

        session.commit()
        session.close()
        return redirect(f'/projects/{project_id}')

    session.close()
    return render_template('new_project.html', title=title, form=creating_project_form,
                           registred_users=registered_users)


@app.route('/projects/<id>')
@login_required
def project(id):
    # Creating db session
    session = db_session.create_session()

    registered_users = len(session.query(User).all())

    project_object = session.query(Project).filter(Project.id == id).first()

    # Check does current user have access to this project
    # If don`t, throw error page

    if current_user not in list(project_object.members) and current_user.role != 'Admin':
        return render_template('error.html', error_code=403, error_message='You don`t have access to this project')

    # If project exist and user have access to it, then return project page
    _project = session.query(Project).filter(Project.id == id).first()
    date_of_creation = _project.created_date
    date_of_creation = f'{date_of_creation.day}-{date_of_creation.month}-{date_of_creation.year} at {date_of_creation.hour}:' \
                       f'{date_of_creation.minute}:{date_of_creation.second}'

    return render_template('project.html', project=project_object)


@app.route('/projects/<id>/manage')
@login_required
def manage_project(id):
    # Creating db session
    session = db_session.create_session()

    registered_users = len(session.query(User).all())

    project_object = session.query(Project).filter(Project.id == id).first()

    # Check does current user have access manage to this project
    # If don`t, throw error page
    print(current_user.project_role(project_object.id))
    if (current_user.project_role(project_object.id) != 'root' or current_user.project_role(
            project_object.id) != 'manager') \
            and current_user.role != 'Admin':
        return render_template('error.html', error_code=403, error_message='You don`t have access to this project')

    return render_template('manage_project.html', project=project_object)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/dev')
def check():
    session = db_session.create_session()
    user = session.query(User).first()
    print(user.project_role)
    user.extra_data = 'somehting'
    print(user.project_role)
    return redirect('/index')


if __name__ == '__main__':
    #    logging.info('Init database session')
    db_session.global_init("db/bugtracker.sqlite")

    # logging.info(f'Running app on {HOST}:{PORT}, DEBUG_MODE: {DEBUG}')
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=1)
