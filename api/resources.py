import hashlib
from flask import jsonify
from flask_restful import reqparse, abort, Resource
from data import db_session
from data.models import *


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
    user_parser = reqparse.RequestParser()
    user_parser.add_argument('username', required=True)
    user_parser.add_argument('password', required=True)

    def get(self, user_id):
        abort_if_not_found(User, user_id)
        session = create_session()
        user = session.query(User).get(user_id)
        return jsonify({'user': user.to_dict(
            only=('role', 'username', 'id')
        )})

    def post(self):
        args = self.user_parser.parse_args()
        session = db_session.create_session()
        user = session.query(User).filter(User.username == args['username']).first()
        if user is not None:
            abort(409, message='User with this username already exists')

        password = hashlib.new('md5', bytes(args['password'], encoding='utf8'))
        user = User(username=args['username'], password_hash=password)
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})


class UserResourceList(Resource):
    def get(self):
        session = create_session()
        users = session.query(User).all()
        return jsonify({'users': [item.to_dict(
            only=('role', 'username', 'id')) for item in users]
        })


class ProjectResource(Resource):
    project_creation_args = reqparse.RequestParser()
    project_creation_args.add_argument('API_KEY', required=True)
    project_creation_args.add_argument('project_name', required=False)
    project_creation_args.add_argument('description', required=False)
    project_creation_args.add_argument('short_tag', required=False)

    def get(self, project_id):
        abort_if_not_found(Project, project_id)
        args = self.project_creation_args.parse_args()
        session = create_session()
        # Get user object by given API KEY
        user_object = session.query(User).filter(User.API_KEY ==
                                                 args["API_KEY"]).first()
        # If user doesn't exist -> throw 404 with message
        if user_object is None:
            abort(404, message=f'User with api key {args["API_KEY"]} not found')

        project = session.query(Project).filter(Project.id == project_id).first()

        # Check if user in project_members
        # If not -> throw 403
        if user_object not in project.members:
            abort(403, message="You don't have access to this project")

        return jsonify({'project': project.to_dict(
            only=('description', 'short_project_tag', 'project_name')
        )
        })

    def post(self, project_id=0):
        session = db_session.create_session()
        args = self.project_creation_args.parse_args()
        if 'short_tag' in args:
            short_tag = args['short_tag']
        else:
            short_tag = args['project_name'][:4]

        # Get user object by given API KEY
        user_object = session.query(User).filter(User.API_KEY ==
                                                 args['API_KEY']).first()
        # If user doesn't exist -> throw 404 with message
        if user_object is None:
            abort(404, message=f'User with api key {args["API_KEY"]} not found')

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
        project_object.members.append(user_object)

        # Commiting changes
        session.merge(project_object)
        session.commit()

        upd = association_table_user_to_project.update().values(project_role='root').where(
            association_table_user_to_project.c.member_id == user_object.id).where(
            association_table_user_to_project.c.project_id == project_object.id)
        project_id = project_object.id
        project_object.add_project_priorities(project_id, ('Critical', 'Major', 'Minor', 'Normal'))
        session.execute(upd)
        session.commit()
        session.close()
        return jsonify({'success': 'OK',
                        'id': f'{project_id}'})


class ProjectResourceList(Resource):
    def get(self):
        session = create_session()
        users = session.query(Project).all()
        return jsonify({'users': [item.to_dict(
            only=('description', 'short_project_tag', 'project_name')) for item in users]
        })
