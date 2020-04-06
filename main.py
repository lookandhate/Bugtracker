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

from flask_restful import Api

# import logging
from data.models import User, Project, Issue
from data import db_session

from src import Forms
from src.model_views import MyAdminIndexView, MyModelView

from api import resources

########################################################################################################################
############################################# Init PORT, HOST AND ADMIN PANEL OBJECTS ##################################
########################################################################################################################

# Init flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'my temp secret key'

db_session.global_init("db/bugtracker.sqlite")

# Init login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Create session for flask-admin
adm_session = db_session.create_session()
admin = Admin(app, index_view=MyAdminIndexView(), template_mode='bootstrap3')

# Add all our models to flask-admin
admin.add_view(MyModelView(User, adm_session))
admin.add_view(MyModelView(Project, adm_session))
admin.add_view(MyModelView(Issue, adm_session))
adm_session.close()

# Init api object
api = Api(app)
# Add api resources
api.add_resource(resources.UserResource, '/api/v0/user/<int:user_id>')
api.add_resource(resources.ProjectResource, '/api/v0/project/<int:project_id>')
api.add_resource(resources.UserResourceList, '/api/v0/users')
api.add_resource(resources.ProjectResourceList, '/api/v0/projects')

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
            flash('You are logged in', 'alert alert-success')
            return redirect('/index')

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


@app.route('/profile/<user_id>/projects')
@login_required
def profile_projects(user_id):
    session = db_session.create_session()
    registered_users = len(session.query(User).all())

    user = session.query(User).filter(User.id == user_id).first()
    return render_template('user_projects.html', user=user)


@app.route('/profile/<user_id>/issues')
@login_required
def profile_issues(user_id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()
    if user is None:
        session.close()
        abort(404)
    if current_user.id == user.id or current_user.is_admin:
        return render_template('user_issues.html', user_obj=user)
    pass


@app.route('/projects/<id>/issues')
@login_required
def project_issues(id):
    session = db_session.create_session()
    # Get project object
    project_object = session.query(Project).filter(Project.id == id).first()
    # Check if project exist
    if project_object is None:
        # Project object None -> project doesn't exist
        # Throw 404
        abort(404)
    # Check does user have access to this project
    if current_user not in project_object.members and not current_user.is_admin:
        # Throw 403
        abort(403)
    return render_template('project_issues.html', project=project_object)


@app.route('/issue/<issue_tag>')
@login_required
def issue(issue_tag):
    session = db_session.create_session()

    issue_object = session.query(Issue).filter(Issue.tracking == issue_tag).first()
    project_obj = issue_object.project[0]
    if current_user not in project_obj.members and not current_user.is_admin:
        session.close()
        abort(403)
    return render_template('issue.html', issue=issue_object)


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
            return redirect('project/new')

        project_object = Project()
        project_object.project_name = creating_project_form.project_name.data
        project_object.description = creating_project_form.project_description.data
        project_object.short_project_tag = creating_project_form.short_project_tag.data if \
            creating_project_form.short_project_tag.data else creating_project_form.project_name.data[:4]

        project_object.members.append(current_user)

        # Commiting changes
        session.merge(project_object)
        session.commit()
        session.close()

        # Re-creating session to update DB state
        session = db_session.create_session()
        project_object = \
            session.query(Project).filter(Project.project_name == creating_project_form.project_name.data).first()

        # Updating association table with new user role and adding priorities
        upd = association_table_user_to_project.update().values(project_role='root').where(
            association_table_user_to_project.c.member_id == current_user.id).where(
            association_table_user_to_project.c.project_id == project_object.id)
        id = project_object.id
        project_object.add_project_priorities(id, ('Critical', 'Major', 'Minor', 'Normal'))
        session.execute(upd)
        session.commit()
        session.close()
        return redirect(f'/projects/{id}')

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

    if current_user not in list(project_object.members) and not current_user.is_admin:
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
            and not current_user.is_admin:
        abort(403)

    return render_template('manage_project.html', form=change_project_property, project=project_object)


@app.route('/projects/<id>/manage/members')
@login_required
def project_members(id):
    session = db_session.create_session()

    project_object = session.query(Project).filter(Project.id == id).first()
    if project_object is None:
        abort(404)
    if current_user.project_role(id) != 'manager' and current_user.project_role(id) != 'root' and not current_user.is_admin:
        abort(403)
    return render_template('project_members.html', project=project_object)


@app.route('/projects/<id>/manage/add_member/')
@login_required
def add_member_to_project(id):
    """

    :param id: Project id in what we want to add new user
    :return:
    """
    try:
        username = request.args['username']
    except KeyError as KE:
        print(KE)
        abort(422)

    session = db_session.create_session()
    if current_user.project_role(id) != 'manager' and current_user.project_role(id) != 'root' and not current_user.is_admin:
        abort(403)

    # Check is user exist
    user = session.query(User).filter(User.username == username).first()
    if user is None:
        # Redirect on members page if user doesn't exist
        flash(f"User {username} doesn't exist", 'alert alert-danger')
        return redirect(f'/projects/{id}/manage/members')

    project_object = session.query(Project).filter(Project.id == id).first()
    user.projects.append(project_object)

    # Update user project role
    # Set it to member
    upd = association_table_user_to_project.update().values(project_role='developer').where(
        association_table_user_to_project.c.member_id == user.id).where(
        association_table_user_to_project.c.project_id == id)
    session.execute(upd)

    # Commiting changes
    session.merge(user)
    session.commit()
    session.close()

    # Redirect on project members page with flash notification
    flash(f'User {username} successfully joined to the project', 'alert alert-success')
    return redirect(f'/projects/{id}/manage/members')


@app.route('/projects/<id>/manage/change_role/', methods=['GET', 'POST'])
@login_required
def change_project_role(id):
    """

    :param id: project id in what we want to make changes
    :return: None
    """
    # Some checks below
    try:
        name = request.args['name']
        role = request.args['role']
        if (role != 'root') and (role != 'manager') and (role != 'developer'):
            raise ValueError(f'Excepted root, manager or developer, got: {role}')
    except KeyError as KE:
        print(KE)
        abort(422)
    except ValueError as VE:
        print(VE)
        abort(422)

    # Only root can change role of users
    session = db_session.create_session()
    if current_user.project_role(id) != 'root' and not current_user.is_admin:
        return abort(403)

    # Get new manager-user object
    user = session.query(User).filter(User.username == name).first()
    # Making old root manager
    current_user.change_project_role(id, 'manager')
    # Making new root
    user.change_project_role(id, 'root')
    flash(f'User {user.username} became {user.project_role(id)} of project', 'alert alert-success')
    session.close()
    return redirect(f'/projects/{id}/manage')


@app.route('/projects/<project_id>/new_issue', methods=['GET', 'POST'])
@login_required
def create_issue(project_id):
    title = 'New issue'
    # Creating db session
    session = db_session.create_session()

    registered_users = len(session.query(User).all())
    project_object = session.query(Project).filter(Project.id == project_id).first()

    # Check does user have access to this project
    if current_user not in project_object.members and not current_user.is_admin:
        abort(403, message="You don't have access to this project")

    create_issue_form = Forms.CreateIssue()
    create_issue_form.priority.choices = [(pr[0], pr[0]) for pr in project_object.get_project_priorities()]
    create_issue_form.state.choices = [(st, st) for st in (
        'Unresolved', 'Fixed', 'Not bug', 'Cant reproduce', 'In progress', 'Fixed', 'Rejected')]

    if create_issue_form.validate_on_submit():
        all_issues = len(project_object.issues)
        issue = Issue()
        issue.tracking = f'{project_object.short_project_tag}-{all_issues + 1}'
        issue.summary = create_issue_form.summary.data
        issue.priority = create_issue_form.priority.data
        issue.state = create_issue_form.state.data
        issue.description = create_issue_form.description.data
        issue.steps_to_reproduce = create_issue_form.steps_to_reproduce.data
        issue.project_id = project_id
        # Append issue to user and project
        project_object.issues.append(issue)

        issue_tag = issue.tracking
        session.merge(issue)
        session.commit()
        session.refresh(issue)
        issue.assignees.append(current_user)
        session.commit()

        return redirect('/issue/{}'.format(issue_tag))

    return render_template('new_issue.html', title=title, project=project_object, form=create_issue_form)


if __name__ == '__main__':
    db_session.global_init("db/bugtracker.sqlite")

    app.run(host=HOST, port=PORT, debug=1)
