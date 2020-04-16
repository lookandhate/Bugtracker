import hashlib
from flask import jsonify, current_app as app
from flask_restful import reqparse, abort, Resource
from data import db_session
from data.models import *

"""
Some notes
If one(or more) of required argument haven't been passed: 400
If user gave API key that doesn't belong to anyone: 401
If requested user doesn't have access to requested entity: 403
If entity doesn't exist: 404
On POST request with creating new entity if there is conflict with existing new and existing
entities(e.g same username with existing user): 409
"""


def abort_if_not_found(cls, entity_id):
    """

    :param cls: Class from data.models that we looking for
    :param entity_id: id of specific object of the class
    :return: abort if not found
    """
    session = db_session.create_session()
    class_object = session.query(cls).get(entity_id)
    if not class_object:
        app.logger.info(f'Instance of {cls} with id = {entity_id} not found')
        abort(404, message=f'Instance of {cls} with id = {entity_id} not found')


class UserResource(Resource):
    """
    Implements interaction with User entity by API
    """
    # Arguments, requirement for API requests
    user_parser = reqparse.RequestParser()
    # Username and password requirement to POST query(registering new User)
    user_parser.add_argument('username', required=False)
    user_parser.add_argument('password', required=False)
    # API_KEY requirement for GET query(get some info about other or self User)
    user_parser.add_argument('API_KEY', required=False)
    # user_id: Integer parameter that represent unique User id about who we want to get information
    user_parser.add_argument('user_id', required=False)

    def get(self):
        """
        Return json with info about User object(username, site-role and user id) if user exists
        Otherwise return 404 if User doesn't exist or 401 if API key incorrect(i.e doesn't exist)
        :return: JSON with username, site-role and user id of user or 404/401 error code
        """

        # Get args and check if user_id been passed
        args = self.user_parser.parse_args()
        if 'user_id' not in args.keys():
            app.logger.info(f'GET to UserResource, not user_id was not not passed')
            abort(400, message='You did not pass user_id argument')

        # Check if user exists
        abort_if_not_found(User, args['user_id'])
        session = create_session()

        # Check if API_KEY in args
        if 'API_KEY' not in args.keys():
            app.logger.info(f'GET to UserResource, not API_KEY was not not passed')
            abort(400, message=f'You did not pass API_KEY parameter')

        # Requested user here means user that own API key
        requested_user = session.query(User).filter(User.API_KEY == args["API_KEY"]).first()
        # Check if API key is equal "None" or user with this api key doesn't exist
        if args["API_KEY"] == 'None' or requested_user is None:
            app.logger.info(f'GET to UserResource, bad API KEY been passed')
            abort(401, message=f'You passed bad API key')

        # All checks are OK, now we can response to user with info that he requested
        user = session.query(User).get(args['user_id'])
        app.logger.info(f'GET to UserResource, response with 200 and {user}')
        return jsonify({'user': user.to_dict(
            only=('role', 'username', 'id')
        )})

    def post(self):
        """
        Create user using username and password that gets from request or response with some error code
        :return: JSON with notification that user registered if all is OK
        Otherwise 409 if we got bad credentials or 409 if user with that username already exists
        """

        args = self.user_parser.parse_args()
        # Check if we have all necessary data
        if 'username' not in args.keys() or 'password' not in args.keys():
            app.logger.info(f'POST to UserResource, username or password have not been passed')
            abort(400, message='Not enough arguments')

        # All data on a place we can go on
        session = db_session.create_session()
        # Check if user with given username already exists
        user = session.query(User).filter(User.username == args['username']).first()
        if user is not None:
            app.logger.info(f'POST to UserResource, user with {args["username"]} already exists')
            abort(409, message='User with this username already exists')
        # Hashing given password using md5
        hashed_password = hashlib.new('md5', bytes(args['password'], encoding='utf8'))
        # And, finally creating new user
        user = User(username=args['username'], hashed_password=hashed_password)
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})


class UserResourceList(Resource):
    user_parser = reqparse.RequestParser()
    user_parser.add_argument('API_KEY', required=True)

    def get(self):
        """
        Return json with info about User object(username, site-role and user id) if user exists
        Otherwise return 404 if User doesn't exist or 401 if API key incorrect(i.e doesn't exist)
        :return: JSON with list of users(username, site-role and user id) 401 error code
        """
        args = self.user_parser.parse_args()
        # Check if API_KEY in args
        if 'API_KEY' not in args.keys():
            app.logger.info('GET to UserResourceList, API_KEY have not been passed')
            abort(400, message=f'You did not pass API_KEY parameter')

        session = create_session()

        # Requested user here means user that own API key
        requested_user = session.query(User).filter(User.API_KEY == args["API_KEY"]).first()
        # Check if API key is equal "None" or user with this api key doesn't exist
        if args["API_KEY"] == 'None' or requested_user is None:
            app.logger.info('GET to UserResourceList, passed bad API_KEY')
            abort(401, message=f'You passed bad API key')

        if not requested_user.is_admin:
            app.logger.info('POST to ProjectResourceList API KEY doesnt belong to ADMIN')
            abort(403, message='Only admin can access this method')

        users = session.query(User).all()
        app.logger.info(f'GET to UserResourceList, response with 200 and List of users')
        return jsonify({'users': [item.to_dict(
            only=('role', 'username', 'id')) for item in users]
        })


class ProjectResource(Resource):
    """
    Implements interaction with Project entity by API
    """
    project_request_args = reqparse.RequestParser()
    project_request_args.add_argument('API_KEY', required=True)
    project_request_args.add_argument('project_id', required=False)
    project_request_args.add_argument('project_name', required=False)
    project_request_args.add_argument('description', required=False)
    project_request_args.add_argument('short_tag', required=False)

    def get(self):
        args = self.project_request_args.parse_args()

        # Check if project_if in args
        if 'project_id' not in args.keys():
            app.logger.info(f'GET to ProjectResource, project_id has not been passed')
            abort(400, message='You did not pass project_id')

        # Check if project with given id exists
        abort_if_not_found(Project, args['project_id'])

        session = create_session()
        # Requested user here means user that own API key
        requested_user = session.query(User).filter(User.API_KEY ==
                                                    args["API_KEY"]).first()

        # If requested user doesn't exist -> throw 401 with message
        if args['API_KEY'] == 'None' or requested_user is None:
            app.logger.info(f'GET to ProjectResource passed bad API_KEY')
            abort(401, message=f'You passed bad API key')

        project = session.query(Project).filter(Project.id == args['project_id']).first()

        # Check if user in project_members
        # If not -> throw 403
        if requested_user not in project.members:
            app.logger.info(f'GET to ProjectResource, user with given API KEY doesnt have access to project')
            abort(403, message="You don't have access to this project")

        return jsonify({'project': project.to_dict(
            only=('description', 'short_project_tag', 'project_name', 'root', 'subsystems',
                  'priorities')
        )
        })

    def post(self):
        """
        Implementation of creating project POST request
        Creating project if API KEY, project name, project_description
        and project tag are correct and assigns it on requested user

        :return: 200 and Project.id if project created correctly
        400 if some if necessary arguments have not been passed
        401 if BAD api key been passed
        409 If project with that project name or project tag already exist
        """
        session = db_session.create_session()
        args = self.project_request_args.parse_args()
        # Check if project name and project description passed
        if 'project_name' not in args.keys() or 'description' not in args.keys():
            app.logger.info('POST to ProjectResource project_name or description have not been passed')
            abort(400, message='You did not passe one(or more) of requirement arguments (project_name, description)')
        # Check if short tag in args
        # If not, short tag will be equal first 5 symbols if project name
        if 'short_tag' in args:
            short_tag = args['short_tag']
        else:
            if len(args['project_name']) < 5:
                short_tag = args['project_name']
            else:
                short_tag = args['project_name'][:4]
        # Get user object by given API KEY
        requested_user = session.query(User).filter(User.API_KEY ==
                                                    args['API_KEY']).first()
        # If user doesn't exist -> throw 401 with message
        if requested_user is None or args['API_KEY'] == 'None':
            app.logger.info('POST to ProjectResource bad API KEY passed')
            abort(401, message=f'You passed bad API key')

        project_object = session.query(Project).filter(Project.project_name == args['project_name']).first()

        # Check if project with that project name exist
        if project_object is not None:
            app.logger.info(f'POST to ProjectResource, Project with this {args["project_name"]} '
                            f'project name already exists')
            abort(409, message='Project with this project name already exists')

        # Check if project with that project short tag exist
        if not session.query(Project).filter(Project.short_project_tag == short_tag).first() is None:
            app.logger.ifno(f'POST to ProjectResource, Project with this {short_tag} short-tag already exists')
            abort(409, message=f'Project with this {short_tag} short-tag already exists')

        project_object = Project(
            project_name=args['project_name'], description=args['description'],
            short_project_tag=args['short_tag'])
        project_object.members.append(requested_user)
        app.logger.info(f'Project {project_object.project_name} created,'
                        f'project_id {project_object.id}. Root - {requested_user.username}')

        # Commiting changes
        session.merge(project_object)
        session.commit()

        upd = association_table_user_to_project.update().values(project_role='root').where(
            association_table_user_to_project.c.member_id == requested_user.id).where(
            association_table_user_to_project.c.project_id == project_object.id)
        project_id = project_object.id
        project_object.add_project_priorities(('Critical', 'Major', 'Minor', 'Normal'))
        session.execute(upd)
        session.commit()
        session.close()
        return jsonify({'success': 'OK',
                        'id': f'{project_id}'})


class ProjectResourceList(Resource):
    project_list_request_args = reqparse.RequestParser()
    project_list_request_args.add_argument('API_KEY', required=True)

    def get(self):
        """
        Checks if requested user is admin, if is -> returns JSON list with all projects information
        In other way 403 error code
        :return: JSON list with all projects if requested user is admin and 403 in other way
        """
        # Request args
        args = self.project_list_request_args.parse_args()
        session = create_session()

        # Requested user here means user that own API key
        requested_user = session.query(User).filter(User.API_KEY == args["API_KEY"]).first()
        # Check if API key is equal "None" or user with this api key doesn't exist
        if args["API_KEY"] == 'None' or requested_user is None:
            app.logger.info('POST to ProjectResourceList bad API KEY passed')
            abort(401, message=f'You passed bad API key')
        # Check if requested user is admin
        if not requested_user.is_admin:
            app.logger.info('POST to ProjectResourceList API KEY doesnt belong to ADMIN')
            abort(403, message='Only admin can access this method')

        projects = session.query(Project).all()
        return jsonify({'projects': [item.to_dict(
            only=('description', 'short_project_tag', 'project_name', 'root')
        ) for item in projects]
        })


class IssueResource(Resource):
    """
    Implements interaction with Issue entity by API
    """
    issue_parser = reqparse.RequestParser()
    issue_parser.add_argument('API_KEY', required=True)
    issue_parser.add_argument('tag', reuired=False)

    issue_parser.add_argument('project_id', required=False)
    issue_parser.add_argument('summary', required=False)
    issue_parser.add_argument('steps_to_reproduce', required=False)
    issue_parser.add_argument('description', required=False)
    issue_parser.add_argument('state', required=False)
    issue_parser.add_argument('priority', required=False)

    def get(self):
        """
        Implementation of GET request to Issue property
        :return: JSON with Issue properties if there is no errors
        Otherwise, 404 if issue does not exist
        403 if user doesnt have access to this Issue
        401 if API key is incorrect
        400 if one of necessary have not been passed
        """
        args = self.issue_parser.parse_args()

        # Check if project_if in args
        if 'tag' not in args.keys():
            app.logger.info(f'GET to IssueResource, tag has not been passed')
            abort(400, message='You did not pass the tag')

        # Check if Issue with given tag exists
        abort_if_not_found(Issue, args['tag'])

        session = create_session()
        # Requested user here means user that own API key
        requested_user: Optional[User] = session.query(User).filter(User.API_KEY ==
                                                                    args["API_KEY"]).first()

        # If requested user doesn't exist -> throw 401 with message
        if args['API_KEY'] == 'None' or requested_user is None:
            app.logger.info(f'GET to IssueResource passed bad API_KEY')
            abort(401, message=f'You passed bad API key')

        issue_object: Optional[Issue] = session.query(Issue).filter(Issue.tracking == args['tag']).first()
        # Check if user has access to the Issue
        if requested_user not in Issue.project.members and not requested_user.is_Admin:
            app.logger.info(f'GET to IssueResource, user with given API KEY doesnt have access to project')
            abort(403, message="You don't have access to this project")

        return jsonify({'issue': issue_object.to_dict(
            only=('tracking', 'priority', 'state', 'description', 'steps_to_reproduce', 'summary', 'project_name',
                  'assign_on'))})

    def post(self):
        """
        Implementation of creating Issue POST request
        Creating issue if all arguments passed, correct and assigns it on requested user

        :return: 200 and Issue.tag if Issue created successfully
        400 if some if necessary arguments have not been passed
        401 if BAD api key been passed
        """

        session = db_session.create_session()
        args = self.project_request_args.parse_args()
        # Check if project name and project description passed
        if 'project_id' not in args.keys() or 'summary' not in args.keys() or 'steps_to_reproduce' not in args.keys() or 'description' not in args.keys() \
                or 'state' not in args.keys() or 'priority' not in args.keys():
            app.logger.info(
                'POST to IssueResource, 400, NotEnoughArguments ')

            abort(400, message='You did'
                               ' not passe one(or more) of requirement arguments'
                               ' (project_id,summary,steps_to_reproduce,description,state,priority))')

        # Get user object
        requested_user: Optional[User] = session.query(User).filter(User.API_KEY == args['API_KEY']).first()
        # Check if user exists
        if requested_user is None or args['API_KEY'] == 'None':
            abort(401, message=f'You passed bad API key')

        # Check if Project exists and user has access to it
        app.logger.info(f'Check if project with project_id={args["project_id"]} exists')
        abort_if_not_found(Project, args['project_id'])

        app.logger.info(f'Project exist, check if user has access to it')
        # Project exists
        project_object = session.query(Project).filter(Project.id == args["project_id"]).first()

        # Check if user has access to it
        if requested_user not in project_object.members and not requested_user.is_admin:
            app.logger.info(f'User {requested_user.username} doesnt have access to Project(project_name='
                            f'{project_object.project_name}, id={args["project_id"]}')
            abort(403, message="You don't have access to this project")

        issue_object = Issue
        all_issues = len(project_object.issues)
        issue_object.tracking = f'{project_object.short_project_tag}-{all_issues + 1}'
        issue_object.summary = args['summary']
        issue_object.priority = args['priority']
        issue_object.state = args['state']
        issue_object.description = args['description']
        issue_object.steps_to_reproduce = args['steps_to_reproduce']
        issue_object.project_id = args['project_id']

        project_object.issues.append(issue_object)

        issue_tag = issue_object.tracking
        session.merge(issue_object)
        session.commit()
        session.refresh(issue_object)
        issue_object.assignees.append(requested_user)
        session.commit()
        return jsonify({'success': 'OK',
                        'tag': f'{issue_tag}'})


class IssueResourceList(Resource):
    """
    Implements get request to all Issues
    """
    issues_list_parser = reqparse.RequestParser()
    issues_list_parser.add_argument('API_KEY', required=True)
    issues_list_parser.add_argument('project_id', required=False)

    def get(self):
        """
        Implementation of GET request to list of Issues
        :return: JSON with list of Issues if there is no errors
        Otherwise, 404 if issue does not exist
        403 if user doesnt have access to this Issue
        401 if API key is incorrect
        """

        args = self.issues_list_parser.parse_args()
        session = db_session.create_session()
        app.logging.info(f'GET IssueResourceList with args{args}')
        # Check if user exists
        requested_user: Optional[User] = session.query(User).filter(User.API_KEY == args['API_KEY']).first()
        if requested_user is None or args['API_KEY'] == 'None':
            app.logging.info(f'GET IssueResourceList User with API key {args["API_KEY"]} doesnt exist, return 400')
            abort(400)
        # If project_id has not been passed that's mean API should return all issues
        if 'project_id' not in args.keys():
            # But list with all issues can access ONLY site admin
            # Check if requested user is admin
            if not requested_user.is_admin:
                app.logging.info(f'GET IssueResourceList without project_id,'
                                 f' {requested_user.username} not an ADMIN, abort with 403')
                abort(403, message='Only admin can access to list of all Issues')

            issues = session.query(Issue).all()
            app.logging.info(f'GET IssueResourceList User({requested_user.username})'
                             f' is admin, return list with all issues')

            return jsonify({'issues': [item.to_dict(
                only=('tracking', 'priority', 'state', 'description', 'steps_to_reproduce', 'summary', 'project_name',
                      'assign_on')
            ) for item in issues]
            })

        else:
            # Check if project exists
            app.logging.info(f'GET IssueResourceList checking if project exists ')
            abort_if_not_found(Project, args['project_id'])
            project_object: Project = session.query(Project).filter(Project.id == args["project_id"])
            app.logging.info('Project exists, check if requested user has access to it')

            # Check if requested user has access to project
            if not requested_user.is_admin or requested_user not in project_object.members:
                app.logging.info(f'GET IssueResourceList, {requested_user}'
                                 f' is admin={requested_user.is_admin},'
                                 f' has access to project={requested_user in project_object.members}')
            app.logging.info(f'Response to {requested_user.username} with the list of Issues')
            # GET all project issues
            issues = project_object.issues
            # And, return list in response
            return jsonify({'issues': [item.to_dict(
                only=('tracking', 'priority', 'state', 'description', 'steps_to_reproduce', 'summary', 'project_name',
                      'assign_on')
            ) for item in issues]
            })
