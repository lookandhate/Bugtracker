import os
import hashlib

from data.models import association_table_user_to_project

from sqlalchemy import update, delete

from flask import render_template, send_from_directory, flash, url_for, redirect, request, abort
from flask import Flask

from flask_login import LoginManager
from flask_login import login_user, login_required, logout_user, current_user

from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView

# import logging
from data.models import User, Project, Issue
from data import db_session

from src import Forms


########################################################################################################################
############################################# Init PORT, HOST AND ADMIN PANEL OBJECTS ##################################
########################################################################################################################


# MyModelView for admin panel
class MyModelView(ModelView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.role == 'Admin'
        return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('access_restricted', from_page='admin', message='Test', code='403'))


# AdminIndexView for admin panel
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.role == 'Admin'
        return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('access_restricted', from_page='admin', message='Test', code='403'))


# Init flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'my temp secret key'

db_session.global_init("db/bugtracker.sqlite")

# Init login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Create session for flask-admin
session = db_session.create_session()
admin = Admin(app, index_view=MyAdminIndexView(), template_mode='bootstrap3')

# Add all our models to flask-admin
admin.add_view(MyModelView(User, session))
admin.add_view(MyModelView(Project, session))
admin.add_view(MyModelView(Issue, session))
session.close()

# Port, IP address and debug mode
PORT, HOST = int(os.environ.get("PORT", 8080)), '0.0.0.0'
DEBUG = True


########################################################################################################################
######################################## APP ROUTES BELOW ##############################################################
########################################################################################################################

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
    title = 'Index'
    session.close()
    return render_template('index.html', title=title, registred_users=registered_users)


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
            flash('User with this username already registered', 'alert alert-danger')
            return render_template('join.html',
                                   form=form)

        # User object for database
        user = User()

        # Hashing password here
        password_hash = hashlib.new('md5', bytes(form.password.data, encoding='utf8'))

        # Filling database with user data
        user.username = form.username.data

        # Here we use not password but its hash
        user.hashed_password = password_hash.hexdigest()

        user.reg_ip = request.remote_addr
        user.last_ip = request.remote_addr

        # Adding user to database
        session.merge(user)
        # Commiting changes
        session.commit()
        session.close()

        flash('Your account has been created and now you are able to log in', 'alert alert-primary')
        return redirect(url_for('index'))
    session.close()
    return render_template('join.html', title=title, form=form, registred_users=registered_users)


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    title = 'Login'
    form = Forms.LoginForm()

    session = db_session.create_session()
    registered_users = len(session.query(User).all())

    if form.validate_on_submit():
        user = session.query(User).filter(User.username == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_ip = request.remote_addr
            session.merge(user)
            session.commit()
            redirect(url_for('index'))

        else:
            flash('Wrong username or password', 'alert alert-danger')
            return render_template('login.html',
                                   form=form)
    return render_template('login.html', title=title, form=form, registred_users=registered_users)


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
    abort(404)
    # return render_template('error.html', error_code=404, error_message='User has been deleted or wasn`t registered',
    #                        registred_users=registered_users)


@app.route('/profile/<user_id>/projects')
@login_required
def profile_projects(user_id):
    session = db_session.create_session()
    registered_users = len(session.query(User).all())

    user = session.query(User).filter(User.id == user_id).first()
    print(user.projects)
    return render_template('user_projects.html', user=user)


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
            flash('Project with that name already created', 'alert alert-danger')
            return redirect(url_for('project/new'))

        project = Project(project_name=creating_project_form.project_name.data,
                          description=creating_project_form.project_description.data)

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
        abort(403, message="You don't have access to this project")

    # If project exist and user have access to it, then return project page
    _project = session.query(Project).filter(Project.id == id).first()
    date_of_creation = _project.created_date
    date_of_creation = f'{date_of_creation.day}-{date_of_creation.month}-{date_of_creation.year} at {date_of_creation.hour}:' \
                       f'{date_of_creation.minute}:{date_of_creation.second}'

    return render_template('project.html', project=project_object, date_of_creation=date_of_creation)


@app.route('/projects/<id>/manage')
@login_required
def manage_project(id):
    # Creating db session
    session = db_session.create_session()

    registered_users = len(session.query(User).all())

    project_object = session.query(Project).filter(Project.id == id).first()
    change_project_property = Forms.ChangeProjectProperties(
        project_name=project_object.project_name,
        project_description=project_object.description,
    )
    project_members = project_object.members
    change_project_property.project_owner.choices = [(m.id, m.username) for m in project_members]

    # Check does current user have access manage to this project
    # If don`t, throw error page
    if (current_user.project_role(project_object.id) != 'root' and current_user.project_role(
            project_object.id) != 'manager') \
            and current_user.role != 'Admin':
        abort(403, message="You don't have access to this project")

    return render_template('manage_project.html', form=change_project_property, project=project_object)


@app.route('/projects/<project_id>/new_issue', methods=['GET', 'POST'])
@login_required
def create_issue(project_id):
    title = 'New issue'
    # Creating db session
    session = db_session.create_session()

    registered_users = len(session.query(User).all())
    project_object = session.query(Project).filter(Project.id == project_id).first()

    # Check does user have access to this project
    if current_user not in project_object.members and current_user.role != 'Admin':
        abort(403, message="You don't have access to this project")

    create_issue_form = Forms.CreateIssue()

    if create_issue_form.validate_on_submit():
        all_issues = len(project_object.issues)
        issue = Issue()
        issue.tracking = f'{project_object.short_project_tag}-{all_issues + 1}'
        issue.priority = create_issue_form.priority.data
        issue.state = create_issue_form.state.data

        # Append issue to user and project
        project_object.issues.append(issue)
        current_user.issues.append(issue)

        session.merge(issue)
        session.commit()
        session.close()
    return render_template('new_issue.html', title=title, project=project_object, form=create_issue_form)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/access_restricted/<from_page>/<message>/<code>')
def access_restricted(from_page, message='You don`t have access to this page', code=403):
    return render_template('error.html', page=from_page, error_code=code, error_message=message)


@app.route('/dev')
def check():
    session = db_session.create_session()
    user = session.query(User).first()
    print(user.project_role)
    user.extra_data = 'somehting'
    print(user.project_role)
    return redirect('/index')


if __name__ == '__main__':
    db_session.global_init("db/bugtracker.sqlite")

    app.run(host=HOST, port=PORT, debug=1)
