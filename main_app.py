import os
import hashlib
import sys

from typing import Optional

from data.models import association_table_user_to_project

from flask import render_template, flash, url_for, redirect, request, abort, send_from_directory
from flask import Flask

from flask_login import LoginManager
from flask_login import login_user, login_required, logout_user, current_user

from flask_admin import Admin

from flask_restful import Api

import logging
from logging.config import dictConfig

from data.models import User, Project, Issue
from data import db_session

from src import forms
from src.model_views import MyAdminIndexView, MyModelView
from src.misc_funcs import generate_random_string
from api import resources

########################################################################################################################
############################################# Init PORT, HOST AND ADMIN PANEL OBJECTS ##################################
########################################################################################################################
# Init logger
logging.basicConfig(filename='app.log')
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.FileHandler',
        'filename': 'app.log',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    },
    'filename': 'app.log'
})

app = Flask('App')
# Secret key generates randomly using generate_random_string from src.misc_funcs
app.config['SECRET_KEY'] = generate_random_string(16)

app.config['SQLITE3_SETTINGS'] = {
    'host': 'db/bugtracker.sqlite'
}

# This for pythonwanywhere.com
if __name__ != '__main__' and not app.testing and os.path.exists('/home/Sadn3ss'):
    app.root_path = os.path.dirname(os.path.abspath(__file__))
    if sys.platform != 'win32':
        app.config['SQLITE3_SETTINGS'] = {
            'host': '/home/Sadn3ss/mysite/db/bugtracker.sqlite'
        }
    else:
        app.config['SQLITE3_SETTINGS'] = {
            'host': 'db/bugtracker.sqlite'
        }

db_session.global_init(app.config['SQLITE3_SETTINGS']['host'])

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
API_VER = '0.8.0'
api.add_resource(resources.UserResource, f'/api/v{API_VER}/user/', f'/api/v{API_VER}/user')
api.add_resource(resources.ProjectResource, f'/api/v{API_VER}/project/', f'/api/v{API_VER}/project')
api.add_resource(resources.UserResourceList, f'/api/v{API_VER}/users/', f'/api/v{API_VER}/users')
api.add_resource(resources.ProjectResourceList, f'/api/v{API_VER}/projects/', f'/api/v{API_VER}/projects')
api.add_resource(resources.IssueResource, f'/api/v{API_VER}/issue/', f'/api/v{API_VER}/issue')
api.add_resource(resources.IssueResourceList, f'/api/v{API_VER}/issues/', f'/api/v{API_VER}/issues')

# Port, IP address and debug mode
PORT, HOST = int(os.environ.get("PORT", 8080)), '0.0.0.0'
DEBUG = True

# Role of users that can change project properties
PROJECT_MANAGE_ROLES = ['root', 'manager']
logger = app.logger


########################################################################################################################
######################################## APP ROUTES BELOW ##############################################################
########################################################################################################################


# Loading current user
@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    loaded_user = session.query(User).get(user_id)
    logger.debug(f'User {loaded_user.username} loaded ')
    session.close()
    return loaded_user


# Main page of app
@app.route('/')
@app.route('/index')
def index():
    session = db_session.create_session()
    title = 'Index'
    session.close()
    return render_template('index.html', title=title)


# Registration page
@app.route('/join', methods=['GET', 'POST'])
def join():
    """
    Register user with given credentials if user with that username doesnt exist
    Otherwise redirect on /join page again
    :return:
    """
    title = 'Join us'
    session = db_session.create_session()
    # Registration form
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        # Creating Database Session
        session = db_session.create_session()

        # checking if user already registered
        if session.query(User).filter(User.username == form.username.data).all():
            session.close()
            logger.info(f'user with username {form.username.data} already registered, redirecting on /join with'
                        f' the flash')
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
        logger.info(f'User {form.username.data} with IP {request.remote_addr} just registered, redirecting on /index')
        flash('Your account has been created and now you are able to log in', 'alert alert-primary')
        return redirect(url_for('index'))
    session.close()
    return render_template('join.html', title=title, form=form)


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login in user if credentials is correct, otherwise redirect back  on login page with appropriate flash-messsage
    :return: Redirect on index if user logged in or back on login if user gave invalid credentials
    """
    title = 'Login'
    form = forms.LoginForm()

    session = db_session.create_session()

    if form.validate_on_submit():
        user = session.query(User).filter(User.username == form.username.data).first()
        # Check if user not is none and hash of password equal to hash in database
        if user and user.check_password(form.password.data):
            # if equal -> login user and redirect to /index
            login_user(user, remember=form.remember_me.data)
            user.last_ip = request.remote_addr
            session.merge(user)
            session.commit()
            logger.info(f'User {user.username} just logged in with ip: {request.remote_addr}\nReg IP:{user.reg_ip}')
            flash('You are logged in', 'alert alert-success')
            return redirect('/index')
        else:
            if user is not None:
                logger.info(
                    f'User {form.username.data} tried to log in with ip: {request.remote_addr}\nReg IP:{user.reg_ip}')
            else:
                logger.info(
                    f'Trying to get access to not existing user account {form.username.data}'
                    f' with IP:{request.remote_addr}')

            flash('Wrong username or password', 'alert alert-danger')
            return render_template('login.html',
                                   form=form)
    return render_template('login.html', title=title, form=form)


# Logout page
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/profile/<user_id>')
@login_required
def profile(user_id):
    """
    Render profile if current user have access to it and User actually exists
    Otherwise throw 404 if user doesnt exist
    Or 403 if current user doesnt have access to this info
    :param user_id: User.id of user whose profile we want to see
    :return:Profile page rendered using profile.html template if all OK
    """
    session = db_session.create_session()

    # Get data that we need
    user = session.query(User).filter(User.id == user_id).first()

    # Checking is user exist
    if user is None:
        # user doesnt exist
        logger.info(f'User with id={user_id} doesnt exist')
        abort(404)

    title = f'{user.username}'
    return render_template('profile.html', title=title, user=user, api_ver=API_VER)

    # If user doesn't exist, throw error page


@app.route('/profile/<user_id>/new_api_key')
@login_required
def regenerate_api_key_page(user_id):
    """
    Change API key of that user if current_user == user
    Otherwise throw 403
    :param user_id: User.id of User who want to change their API key
    :return: redirect on profile page
    """
    session = db_session.create_session()
    user_object = session.query(User).filter(User.id == user_id).first()
    if current_user != user_object:
        abort(403)
    logger.info(f'Regenerate API key of {user_object.username}')
    user_object.regenerate_API_key()
    flash('Your API key changed', 'alert alert-success')
    return redirect(f'/profile/{user_id}')


@app.route('/profile/<user_id>/projects')
@login_required
def profile_projects(user_id):
    """
    Take user_id and return page with all user projects if user have access to this info
    Otherwise abort with 403 code
    :param user_id: User.id whom projects we want to see
    :return: Page with all user projects if current_user == User or current_user.is_admin
    """
    session = db_session.create_session()

    user = session.query(User).filter(User.id == user_id).first()
    # Check if user actually exist
    if user is None:
        # Throw 404
        logger.info(f'User with id={user_id} doesnt exist')
        abort(404)
    if current_user.id != user.id and not current_user.is_admin:
        # Current user doesnt have access to other users issues, throw 403
        logger.info(f'User {current_user.username} doesnt have access to {user.username}`s projects')
        abort(403)
    title = f"{user.username}'s projects"
    return render_template('user_projects.html', title=title, user=user)


@app.route('/profile/<user_id>/issues')
@login_required
def profile_issues(user_id):
    """
    Take user_id and return page with all user issues if user have access to this info
    Otherwise abort with 403 code
    :param user_id: User.id whom issue we want to see
    :return: Page with all user issues if current_user == User or current_user.is_admin
    """
    session = db_session.create_session()
    user = session.query(User).filter(User.id == user_id).first()

    # Check if user actually exists
    if user is None:
        # User doesn't exist -> throw 404
        session.close()
        logger.info(f'User with User.id={user_id} doesnt exist')
        abort(404)
    if current_user.id != user.id and not current_user.is_admin:
        # Current user doesnt have access to other users issues, throw 403
        logger.info(f'User {current_user.username} doesnt have access to {user.username}`s issues')
        abort(403)

    return render_template('user_issues.html', user=user)


@app.route('/projects/<project_id>/issues')
@login_required
def project_issues(project_id):
    session = db_session.create_session()
    # Get project object
    project_object = session.query(Project).filter(Project.id == project_id).first()
    # Check if project exist
    if project_object is None:
        # Project object is None -> project doesn't exist, throw 404
        abort(404)
    # Check does user have access to this project
    if current_user not in project_object.members and not current_user.is_admin:
        # Current user doesn't have access to this project, throw 403
        abort(403)
    return render_template('project_issues.html', project=project_object)


@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    """
    Creating project with current_user as project_root
    :return: redirect on project page when project created or creating project page on filling create project fields
    """
    title = 'Create project'
    creating_project_form = forms.CreateProject()
    session = db_session.create_session()
    registered_users = len(session.query(User).all())

    if creating_project_form.validate_on_submit():
        # Check if project with that project name or project tag already exist
        if session.query(Project).filter(Project.project_name == creating_project_form.project_name.data).all() or \
                session.query(Project).filter(
                    Project.short_project_tag == creating_project_form.short_project_tag.data).all():
            session.close()
            logger.info(f'Project with project_name={creating_project_form.project_name.data} or'
                        f' project_tag={creating_project_form.short_project_tag.data} already exist')
            flash('Project with that name already created', 'alert alert-danger')
            return redirect('/project/new')

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
        project_id = project_object.id
        project_object.add_project_priorities(('Critical', 'Major', 'Minor', 'Normal'))
        session.execute(upd)
        session.commit()

        logger.info(f'User {current_user.username} just created the project {project_object.project_name} with ID'
                    f' {project_id}')

        session.close()
        return redirect(f'/projects/{project_id}')

    session.close()
    return render_template('new_project.html', title=title, form=creating_project_form,
                           registred_users=registered_users)


@app.route('/projects/<project_id>')
@login_required
def project(project_id):
    """
    Takes Project.id of what we want to see project
    If project doesn't exist -> throw 404
    If user doesn't have access to project -> throw 403
    :param project_id: Of which project we want to see summary page
    :return: rendered page using project.html
    """
    # Creating db session
    session = db_session.create_session()

    registered_users = len(session.query(User).all())

    project_object = session.query(Project).filter(Project.id == project_id).first()

    # Check does current user have access to this project
    # If don`t, throw error page
    if project_object is None:
        logger.info(f'Project with Project.id {project_id} doesnt exist')
        abort(404)

    if current_user not in project_object.members and not current_user.is_admin:
        logger.info(f'User {current_user.username} doesnt have access to Project(project_name={project_object.name},'
                    f'project_id={project_object.id})')
        abort(403)

    # If project exist and user have access to it, then return project page
    date_of_creation = project_object.created_date
    date_of_creation = f'{date_of_creation.day}-{date_of_creation.month}-{date_of_creation.year} at {date_of_creation.hour}:' \
                       f'{date_of_creation.minute}:{date_of_creation.second}'

    return render_template('project.html', project=project_object, date_of_creation=date_of_creation)


@app.route('/projects/<project_id>/manage')
@login_required
def manage_project(project_id):
    """
    Takes project_id in which we want to manage members
    If project doesnt exist -> throw 404
    If user doesnt have access for managing project -> throw 403
    If all okey -> render page using manage_project.html template
    :param project_id: Project.id in which want to manage members
    :return: Page rendered using project_members.html template
    """
    # Creating db session
    session = db_session.create_session()

    project_object = session.query(Project).filter(Project.id == project_id).first()

    # Check does project actually exist
    if project_object is None:
        logger.info(f'Project with Project.id={project_id} doesnt exist')
        abort(404)

    change_project_property = forms.ChangeProjectProperties(
        project_name=project_object.project_name,
        project_description=project_object.description,
    )
    project_members = project_object.members
    change_project_property.project_owner.choices = [(m.id, m.username) for m in project_members]

    # Check does current user have access manage to this project
    # If don`t, throw error page
    if current_user.project_role(project_object.id) not in PROJECT_MANAGE_ROLES and not current_user.is_admin:
        logger.info(f'User {current_user.username} doenst have access to manage Project(project_id={project_id}'
                    f'project_name={project_object.project_name}')
        abort(403)

    return render_template('manage_project.html', form=change_project_property, project=project_object)


@app.route('/projects/<project_id>/manage/members')
@login_required
def project_members(project_id):
    """
    Takes project_id in which we want to see members
    :param project_id: Project.id in which want to see members
    :return: Page rendered using project_members.html template
    """
    session = db_session.create_session()

    project_object = session.query(Project).filter(Project.id == project_id).first()
    if project_object is None:
        logger.info(f'Project with Project.id {project_id} doesnt exist')
        abort(404)
    if current_user.project_role(project_object.id) not in PROJECT_MANAGE_ROLES and not current_user.is_admin:
        logger.info(f'User {current_user.username} dosent have access to Project(project_name='
                    f'{project_object.project_name}, project_id={project_object.id}')
        abort(403)
    return render_template('project_members.html', project=project_object)


@app.route('/projects/<project_id>/manage/add_member/')
@login_required
def add_member_to_project(project_id):
    """
    Takes Project.id of Project in which we want to add new user
     and User.username of user who we want to add to project

    :param project_id: Project.id in what we want to add new user
    :return: redirect on manage project members page in anyway(except if project doesnt exist( 404 then )
    """
    try:
        username = request.args['username']
    except KeyError as KE:
        logger.error(KE)
        abort(422)

    session = db_session.create_session()
    if current_user.project_role(project_id) not in PROJECT_MANAGE_ROLES and not current_user.is_admin:
        abort(403)

    # Check is user exist
    user = session.query(User).filter(User.username == username).first()
    if user is None:
        # Redirect on members page if user doesn't exist
        flash(f"User {username} doesn't exist", 'alert alert-danger')
        return redirect(f'/projects/{project_id}/manage/members')

    project_object = session.query(Project).filter(Project.id == project_id).first()
    # Check does project actually exist
    if project_object is None:
        logger.info(f'Project with Project.id == {project_id} doesnt exist')
        abort(404)
    user.projects.append(project_object)

    # Update user project role
    # Set it to member
    user.change_project_role(project_id, 'developer')

    logger.info(f'User {current_user.username} just added {username} to {project_id}')

    # Commiting changes
    session.merge(user)
    session.commit()
    session.close()

    # Redirect on project members page with flash notification
    flash(f'User {username} successfully joined to the project', 'alert alert-success')
    return redirect(f'/projects/{project_id}/manage/members')


@app.route('/projects/<project_id>/manage/remove_user/')
@login_required
def remove_user_from_project(project_id):
    """
    Takes project id and name of user who we want to delete from Project with Project.id == project_id
    :param project_id: Project.id in which we want to delete user
    :return: redirect on manage Project members page
    """
    # Check passed name arg
    try:
        name = request.args['name']
    except KeyError as KE:
        abort(422)
    session = db_session.create_session()

    # Get user object
    user = session.query(User).filter(User.username == name).first()
    # Check if root trying delete himself from project
    if user == current_user:
        flash('You cant just remove yourself from project', 'alert alert-danger')
        return redirect(f'/projects/{project_id}/manage/members')

    # Get project object
    project_object = session.query(Project).filter(Project.id == project_id).first()

    # Check does user and project actually exists
    if user is None or project_object is None:
        # If doesn't -> throw 404
        logger.info(f'User or project doesnt exist(Project={project_object}, User={user})')
        abort(404)

    # Check does current user have access
    if current_user.project_role(project_object.id) not in PROJECT_MANAGE_ROLES and not current_user.is_admin:
        abort(403)

    # And remove project from user project list
    user.projects.remove(project_object)
    logger.info(f'User {current_user.username} deleted {user.username} from project {project_object.project_name}'
                f' with ID {project_id}')

    session.merge(user)
    session.commit()

    flash(f'User {user.username} has been removed from f{project_object.project_name}', 'alert alert-success')
    return redirect(f'/projects/{project_id}/manage/members')


@app.route('/projects/<project_id>/manage/change_role/', methods=['GET', 'POST'])
@login_required
def change_project_role(project_id):
    """

    :param project_id: project id in what we want to make changes
    :return: None
    This route takes project id, name and role, and changes user project role in Project with Project.id == project_id
    """
    # Some checks below
    try:
        name = request.args['name']
        role = request.args['role']
        if (role != 'root') and (role != 'manager') and (role != 'developer'):
            raise ValueError(f'Excepted root, manager or developer, got: {role}')
    except KeyError as KE:
        logger.error(KE)
        abort(422)
    except ValueError as VE:
        logger.error(VE)
        abort(422)

    session = db_session.create_session()

    # Check if project actually exists
    project_object = session.query(Project).filter(Project.id == project_id).first()
    if project_object is None:
        logger.warning(f'Project with id {project_id} doesnt exist')
        abort(404)

    # Only root and manager can change role of users
    if current_user.project_role(project_id) not in PROJECT_MANAGE_ROLES and not current_user.is_admin:
        logger.info(
            f'User {current_user.username}(is_admin={current_user.is_admin}) tried change project roles(project'
            f' root:{project_object.get_root()}')
        return abort(403)

    # Current user either admin, project manager or root, can go on
    user_object_to_change: User = session.query(User).filter(User.username == name).first()

    # Check if user to role change actually exists
    if user_object_to_change is None:
        # If not throw 404
        logger.info(f'User with {name} doesnt exists, throw 404')
        abort(404)

    # User exists, can go on
    # If role root -> we gotta make old root manager
    if role == 'root':
        # Check if current user is actually root or site admin
        if not current_user.is_admin and project_object.get_root() != current_user:
            # Current user neither project root nor app admin -> throw 403
            logger.info(
                f'User {current_user.username}(is_admin={current_user.is_admin}) tried change project root(project'
                f' root:{project_object.get_root()}')
            abort(403)

        # All checks behind: user exists, current user either site admin or project root
        logger.info(f'Changing on root, project id:{project_id}')
        # Making new root
        user_object_to_change.change_project_role(project_id, role)
        # Making Old root a project manager
        logger.info(f'{project_object.get_root().username} became manager, new root'
                    f' - {user_object_to_change.username}')

        project_object.get_root().change_project_role(project_id, 'manager')
        # Making flash notification that we successfully changed project root
        flash(f'User {user_object_to_change.username} became {user_object_to_change.project_role(project_id)}'
              f' of project', 'alert alert-success')
        session.close()

    if role in ('manager', 'developer'):
        # Check if current user is actually root or site admin
        if not current_user.is_admin and project_object.get_root() != current_user:
            # Current user neither project root nor app admin -> throw 403
            logger.info(
                f'User {current_user.username}(is_admin={current_user.is_admin}) tried change project {role}, (project'
                f' root-{project_object.get_root().username}')
            abort(403)
        # All checks behind: user exists, current user either site admin or project root
        logger.info(
            f'Changing {user_object_to_change.username} role in {project_object.prpject_name}(ID = {project_id}) '
            f'Old role: {user_object_to_change.project_role(project_id)}, new role: {role}'
        )
        # Making flash notification that we successfully changed user role
        flash(f'User {user_object_to_change.username} became {user_object_to_change.project_role(project_id)}'
              f' of project', 'alert alert-success')
        session.close()

    return redirect(f'/projects/{project_id}/manage')


@app.route('/issue/<issue_tag>')
@login_required
def issue(issue_tag):
    """
    This function takes issue_tag as a parameter, checks does current user have access to this issue
     and if he does returns page with this issue/
     If doesn't -> abort connection with 403 error code
    :param issue_tag: Unique tag of issue
    :return: Page that rendered from issue.html template
    """
    session = db_session.create_session()
    # Get issue object from database
    issue_object = session.query(Issue).filter(Issue.tracking == issue_tag).first()
    # Check if issue with that tag actually exists
    if issue_object is None:
        # If not -> throw 404
        logger.info(f'Issue with {issue_tag} doesnt exist, throw 404')
        abort(404)
    # If issue exists then check does current user actually have access to the issue
    project_obj = issue_object.project[0]  # Using index because .project contain list of projects
    if current_user not in project_obj.members and not current_user.is_admin:
        # User doesnt have access to project -> throw 403
        session.close()
        logger.info(f'User {current_user.username} doesnt have access to Issue with tag {issue_tag}')
        abort(403)
    # User have access -> render template
    return render_template('issue.html', issue=issue_object)


@app.route('/projects/<project_id>/new_issue', methods=['GET', 'POST'])
@login_required
def create_issue(project_id):
    """
    Takes project_id and creates new issue_object there if user have access to this project
    Otherwise throws 403 code

    :param project_id: project id in which we want to create new issue_object
    :return: Page rendered using new_issue.html template
    """
    title = 'New issue'
    # Creating db session
    session = db_session.create_session()

    project_object = session.query(Project).filter(Project.id == project_id).first()
    # Check does project with this project_id actually exist
    if project_object is None:
        # If project doesnt exist -> throw 404
        logger.info(f'Project with {project_id} doesnt exist, throw 404')
        session.close()
        abort(404)

    # Check does user have access to this project
    if current_user not in project_object.members and not current_user.is_admin:
        logger.info(f'User {current_user.username} doesnt have access to Project(project_name='
                    f'{project_object.project_name}, id={project_id}')
        abort(403, message="You don't have access to this project")

    create_issue_form = forms.CreateIssue()
    create_issue_form.priority.choices = [(pr[0], pr[0]) for pr in project_object.get_project_priorities()]
    create_issue_form.state.choices = [(st, st) for st in (
        'Unresolved', 'Fixed', 'Not bug', 'Cant reproduce', 'In progress', 'Fixed', 'Rejected')]

    if create_issue_form.validate_on_submit():
        all_issues = len(project_object.issues)
        issue_object = Issue()
        issue_object.tracking = f'{project_object.short_project_tag}-{all_issues + 1}'
        issue_object.summary = create_issue_form.summary.data
        issue_object.priority = create_issue_form.priority.data
        issue_object.state = create_issue_form.state.data
        issue_object.description = create_issue_form.description.data
        issue_object.steps_to_reproduce = create_issue_form.steps_to_reproduce.data
        issue_object.attachments = create_issue_form.attachments.data
        issue_object.project_id = project_id
        # Append issue_object to user and project
        project_object.issues.append(issue_object)

        issue_tag = issue_object.tracking
        session.merge(issue_object)
        session.commit()
        session.refresh(issue_object)
        issue_object.assignees.append(current_user)
        session.commit()

        return redirect(f'/issue/{issue_tag}')

    return render_template('new_issue.html', state='New issue_object', title=title, project=project_object,
                           form=create_issue_form)


@app.route('/issue/<issue_tag>/change', methods=['GET', 'POST'])
@login_required
def change_issue(issue_tag: str):
    """
    Takes issue_tag, checks does user have access to project in which we want to change issue
    If user has -> change issue
    If issue doesn't exist -> throw 404
    IF user doesn't have access -> throw 403

    :param issue_tag: Issue that we want to change
    :return: Page rendered using new_issue.html with new issue data
    """
    session = db_session.create_session()

    issue_object: Optional[Issue] = session.query(Issue).filter(Issue.tracking == issue_tag).first()
    # Check does issue with that tag actually exist
    if issue_object is None:
        # If it doesn`t -> throw 404 error page
        logger.info(f'Issue with tag {issue_tag} doesnt exist, throw 404')
        session.close()
        abort(404)

    # Check does user have access to the issue
    # Using index because .project contain list of projects
    if current_user not in issue_object.project[0].members and not current_user.is_admin:
        logger.info(f'User {current_user.username} doesnt have access to issue with tag {issue_tag}')
        session.close()
        abort(403)

    title = f'Change {issue_object.tracking}'
    # Creating issue form
    change_issue_form: forms.CreateIssue = forms.CreateIssue()
    change_issue_form.submit.label = 'Update'
    change_issue_form.priority.choices = [(pr[0], pr[0]) for pr in issue_object.project[0].get_project_priorities()]
    change_issue_form.state.choices = [(st, st) for st in (
        'Unresolved', 'Fixed', 'Not bug', 'Cant reproduce', 'In progress', 'Fixed', 'Rejected')]

    if request.method == 'GET':
        # IMPORTANT: USING GET CONDITION BECAUSE WITHOUT IT DATA FROM DATABASE REWRITES DATA IN FORM
        # Assign data from database to form fields
        change_issue_form.summary.data, change_issue_form.priority.data, change_issue_form.state.data, \
        change_issue_form.description.data, change_issue_form.steps_to_reproduce.data, change_issue_form.attachments.data = \
            issue_object.summary, issue_object.priority, issue_object.state, issue_object.description, \
            issue_object.steps_to_reproduce, issue_object.attachments

    if change_issue_form.validate_on_submit():
        session = db_session.create_session()
        issue_object = session.query(Issue).filter(Issue.tracking == issue_tag).first()
        if issue_object:
            issue_object.summary, issue_object.priority, issue_object.state, issue_object.description, \
            issue_object.steps_to_reproduce, issue_object.attachments = \
                change_issue_form.summary.data, change_issue_form.priority.data, change_issue_form.state.data, \
                change_issue_form.description.data, change_issue_form.steps_to_reproduce.data, \
                change_issue_form.attachments.data

            session.commit()
            flash(f'Info about issue {issue_object.tracking} successfully updated', 'alert alert-success')
            return redirect(f'/issue/{issue_object.tracking}')
        else:
            abort(404)

    return render_template('new_issue.html', state='Edit issue', title=title, project=issue_object.project[0],
                           form=change_issue_form)


@app.route('/api')
@login_required
def api_page():
    return render_template('api.html', api_ver=API_VER, user=current_user)


@app.route('/app_logs')
@login_required
def get_app_logs():
    """
    Checks if current user is admin and if he is sends app logs
    If he isn't -> redirect to index with flash
    :return:
    """
    if current_user.is_admin:
        return send_from_directory(app.root_path, 'app.log')
    flash('Only admin can do that' 'alert alert-danger')
    return redirect('index')


def main(host=HOST, port=PORT, debug=1):
    db_session.global_init(app.config['SQLITE3_SETTINGS']['host'])
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main(debug=False)
