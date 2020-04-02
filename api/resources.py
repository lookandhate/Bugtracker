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
    object = session.query(cls).get(id)
    if not object:
        abort(404, message=f'Instance of {cls} with id = {id} not found')


class UserResource(Resource):
    def get(self, user_id):
        abort_if_not_found(User, user_id)
        session = create_session()
        user = session.query(User).get(user_id)
        return jsonify({'user': user.to_dict(
            only=('role', 'username', 'id')
        )})


class UserResourceList(Resource):
    def get(self):
        session = create_session()
        users = session.query(User).all()
        return jsonify({'users': [item.to_dict(
            only=('role', 'username', 'id')) for item in users]
        })


class ProjectResource(Resource):
    def get(self, project_id):
        abort_if_not_found(Project, project_id)
        session = create_session()
        project = session.query(project_id).get()
        return jsonify({'project': project.to_dict(
            only=('description', 'short_project_tag', 'project_name')
        )
        })


class ProjectResourceList(Resource):
    def get(self):
        session = create_session()
        users = session.query(Project).all()
        return jsonify({'users': [item.to_dict(
            only=('description', 'short_project_tag', 'project_name')) for item in users]
        })
