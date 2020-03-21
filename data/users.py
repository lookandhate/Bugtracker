import datetime
import sqlalchemy
import hashlib

from .db_session import SqlAlchemyBase

from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    def check_password(self, password):
        # Here we checking if inputed password hash equal to hash in our database

        h = hashlib.new('md5', bytes(password, encoding='utf8'))
        return h.hexdigest() == self.hashed_password


class Project(SqlAlchemyBase):
    __tablename__ = 'projects'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)

    project_name = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    members = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    issues = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)


class Issue(SqlAlchemyBase):
    __tablename__ = 'issues'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True, unique=True)
    project = sqlalchemy.Column(sqlalchemy.String, index=True)
    tracking = sqlalchemy.Column(sqlalchemy.String, unique=True)
    priority = sqlalchemy.Column(sqlalchemy.String, index=True)
    state = sqlalchemy.Column(sqlalchemy.String)
    assignee = sqlalchemy.Column(sqlalchemy.String)
