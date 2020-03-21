import os
import hashlib

from flask import render_template, send_from_directory, flash, url_for, redirect
from flask import Flask

from flask_login import LoginManager
from flask_login import login_user, login_required, logout_user, current_user

# import logging
from data.users import User, Project, Issue
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

        flash('Your account has been created and now you are able to log in', 'success')
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
    username = session.query(User.username).filter(User.id == user_id).first()

    # Checking is user exist
    if username is not None:
        username = username[0]
        projects = session.query(User.projects).filter(User.id == user_id).first()[0]
        role = session.query(User.role).filter(User.id == user_id).first()[0]
        date_of_reg = session.query(User.created_date).filter(User.id == user_id).first()[0]

        # Unpacking datetime.datetime object on time units
        date_of_reg = f'{date_of_reg.day}-{date_of_reg.month}-{date_of_reg.year} at {date_of_reg.hour}:' \
                      f'{date_of_reg.minute}:{date_of_reg.second}'

        session.close()
        return render_template('profile.html', title=f'{username}', id=user_id, username=username, projects=projects,
                               role=role,
                               date_of_reg=date_of_reg, registred_users=registered_users)

    # If user doesn't exist, throw error page
    return render_template('error.html', error_code=404, error_message='User has been deleted or wasn`t registered',
                           registred_users=registered_users)


@app.route('/profile/<user_id>/projects')
@login_required
def profile_projects(user_id):
    # TODO: Implement user Projects
    pass


@app.route('/profile/<user_id>/issues')
@login.required
def profile_issues(user_id):
    # TODO: Implement user Issues
    pass



@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    title = 'Create project'
    creating_proj_form = Forms.CreateProject()
    session = db_session.create_session()
    registred_users = len(session.query(User).all())

    if creating_proj_form.validate_on_submit():
        if session.query(Project).filter(Project.project_name == creating_proj_form.project_name.data).all():
            session.close()
            return render_template('index.html',
                                   message="Project with that name already created",
                                   form=creating_proj_form)

        project = Project()
        project.project_name = creating_proj_form.project_name.data
        project.members = f'{current_user.username}:root;'

        # Commiting changes
        session.merge(project)
        session.commit()
        session.close()

        # Re-creating session to update DB state
        session = db_session.create_session()
        proj_id = \
            session.query(Project.id).filter(Project.project_name == creating_proj_form.project_name.data).first()[0]
        session.close()
        return redirect(f'/projects/{proj_id}')
    session.close()
    return render_template('new_project.html', title=title, form=creating_proj_form, registred_users=registred_users)


@app.route('/projects/<id>')
@login_required
def project(id):
    # Creating db session
    session = db_session.create_session()

    registered_users = len(session.query(User).all())

    # Get all project members
    project_members = session.query(Project.members).filter(Project.id == id).first()

    # Check does project exist
    # If not then throw error page
    if project_members is None:
        return render_template('error.html', error_code=404, error_message='This project doesn`t exist',
                               registred_users=registered_users)

    # Check does current user have access to this project
    # If don`t, throw error page
    if str(current_user.username) not in project_members[0] or current_user.role != 'Admin':
        return render_template('error.html', error_code=403, error_message='You don`t have access to this project')

    # If project exist and user have access to it, then return project page
    _project = session.query(Project).filter(Project.id == id).first()
    date_of_creation = _project.created_date
    date_of_creation = f'{date_of_creation.day}-{date_of_creation.month}-{date_of_creation.year} at {date_of_creation.hour}:' \
                       f'{date_of_creation.minute}:{date_of_creation.second}'

    project_members = str(_project.members).split(';')
    if '' in project_members:
        project_members.pop(project_members.index(''))

    return render_template('project.html', id=id, project_name=_project.project_name,
                           project_members=project_members,
                           project_issues=str(_project.issues).split(';'),
                           date_of_creation=date_of_creation)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    #    logging.info('Init database session')
    db_session.global_init("db/bugtracker.sqlite")

    # logging.info(f'Running app on {HOST}:{PORT}, DEBUG_MODE: {DEBUG}')
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=1)
