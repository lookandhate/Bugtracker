import hashlib
from flask import jsonify
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
            abort(400, message='You did not pass user_id argument')

        # Check if user exists
        abort_if_not_found(User, args['user_id'])
        session = create_session()

        # Check if API_KEY in args
        if 'API_KEY' not in args.keys():
            abort(400, message=f'You did not pass API_KEY parameter')

        # Requested user here means user that own API key
        requested_user = session.query(User).filter(User.API_KEY == args["API_KEY"]).first()
        # Check if API key is equal "None" or user with this api key doesn't exist
        if args["API_KEY"] == 'None' or requested_user is None:
            abort(401, message=f'You passed bad API key')

        # All checks are OK, now we can response to user with info that he requested
        user = session.query(User).get(args['user_id'])
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
        if not ('username' in args.keys() and 'password' in args.keys()):
            abort(400, message='Not enough arguments')

        # All data on a place we can go on
        session = db_session.create_session()
        # Check if user with given username already exists
        user = session.query(User).filter(User.username == args['username']).first()
        if user is not None:
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
            abort(400, message=f'You did not pass API_KEY parameter')

        session = create_session()

        # Requested user here means user that own API key
        requested_user = session.query(User).filter(User.API_KEY == args["API_KEY"]).first()
        # Check if API key is equal "None" or user with this api key doesn't exist
        if args["API_KEY"] == 'None' or requested_user is None:
            abort(401, message=f'You passed bad API key')

        users = session.query(User).all()
        return jsonify({'users': [item.to_dict(
            only=('role', 'username', 'id')) for item in users]
        })


class ProjectResource(Resource):
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
            abort(400, message='You did not pass project_id')

        # Check if project with given id exists
        abort_if_not_found(Project, args['project_id'])

        session = create_session()
        # Requested user here means user that own API key
        requested_user = session.query(User).filter(User.API_KEY ==
                                                    args["API_KEY"]).first()

        # If requested user doesn't exist -> throw 401 with message
        if args['API_KEY'] == 'None' or requested_user is None:
            abort(401, message=f'You passed bad API key')

        project = session.query(Project).filter(Project.id == args['project_id']).first()

        # Check if user in project_members
        # If not -> throw 403
        if requested_user not in project.members:
            abort(403, message="You don't have access to this project")

        return jsonify({'project': project.to_dict(
            only=('description', 'short_project_tag', 'project_name')
        )
        })

    def post(self):
        session = db_session.create_session()
        args = self.project_request_args.parse_args()
        # Check if project name and project description passed
        if not ('project_name' in args.keys() and 'description' in args.keys()):
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
            abort(401, message=f'You passed bad API key')

        project_object = session.query(Project).filter(Project.project_name == args['project_name']).first()

        # Check if project with that project name exist
        if project_object is not None:
            abort(409, message='Project with this project name already exists')
        # Check if project with that project short tag exist
        if not session.query(Project).filter(Project.short_project_tag == short_tag).first() is None:
            abort(409, message=f'Project with this {short_tag} short-tag already exists')

        project_object = Project(
            project_name=args['project_name'], description=args['description'],
            short_project_tag=args['short_tag'])
        project_object.members.append(requested_user)

        # Commiting changes
        session.merge(project_object)
        session.commit()

        upd = association_table_user_to_project.update().values(project_role='root').where(
            association_table_user_to_project.c.member_id == requested_user.id).where(
            association_table_user_to_project.c.project_id == project_object.id)
        project_id = project_object.id
        project_object.add_project_priorities(project_id, ('Critical', 'Major', 'Minor', 'Normal'))
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
            abort(401, message=f'You passed bad API key')
        # Check if requested user is admin
        if not requested_user.is_admin:
            abort(403,message='Only admin can access this method')

        projects = session.query(Project).all()
        return jsonify({'users': [item.to_dict(
            only=('description', 'short_project_tag', 'project_name')) for item in projects]
        })
