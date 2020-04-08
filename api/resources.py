import hashlib
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource
from data import db_session
from data.models import *


def abort_if_not_found(cls, id):
    """

    :param cls: Class from data.models that we looking for
    :param id: id of specific object of the class
    :return: abort if not found
    """
    session = db_session.create_session()
    class_object = session.query(cls).get(id)
    if not class_object:
        abort(404, message=f'Instance of {cls} with id = {id} not found')


class UserResource(Resource):
    user_parser = reqparse.RequestParser()
    user_parser.add_argument('username', require=True)
    user_parser.add_argument('password', require=True)

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
    project_creation_args.add_argument('project_name', required=True)
    project_creation_args.add_argument('description', required=True)
    project_creation_args.add_argument('short_tag', required=False)

    def get(self, project_id):
        abort_if_not_found(Project, project_id)
        session = create_session()
        project = session.query(project_id).get()
        return jsonify({'project': project.to_dict(
            only=('description', 'short_project_tag', 'project_name')
        )
        })

    def post(self):
        session = db_session.create_session()
        args = self.project_creation_args.parse_args()
        if 'short_tag' in args:
            short_tag = args['short_tag']
        else:
            short_tag = args['project_name'][:4]
        project_object = session.query(Project).filter(Project.project_name == args['project_name'])
        if project_object is not None:
            abort(409, message='Project with this project name already exists')
        project_object = Project(
            project_name=args['project_name'], description=args['description'],
            short_project_tag=args['short_project_tag']
        )
        session.add(project_object)
        session.commit()
        return jsonify({'success': 'OK'})


class ProjectResourceList(Resource):
    def get(self):
        session = create_session()
        users = session.query(Project).all()
        return jsonify({'users': [item.to_dict(
            only=('description', 'short_project_tag', 'project_name')) for item in users]
        })
