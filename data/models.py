import datetime
import sqlalchemy
import hashlib

from .db_session import SqlAlchemyBase

from sqlalchemy import orm
from flask_login import UserMixin

association_table_user_to_issue = sqlalchemy.Table('user_to_issue', SqlAlchemyBase.metadata,
                                                   sqlalchemy.Column('user_id', sqlalchemy.Integer,
                                                                     sqlalchemy.ForeignKey('users.id')),
                                                   sqlalchemy.Column('issue_id', sqlalchemy.Integer,
                                                                     sqlalchemy.ForeignKey('issues.id'))
                                                   )
association_table_user_to_project = sqlalchemy.Table('user_to_project', SqlAlchemyBase.metadata,
                                                     sqlalchemy.Column('member_id', sqlalchemy.Integer,
                                                                       sqlalchemy.ForeignKey('users.id')),
                                                     sqlalchemy.Column('project_id', sqlalchemy.Integer,
                                                                       sqlalchemy.ForeignKey('projects.id')),
                                                     sqlalchemy.Column('project_role', sqlalchemy.String)
                                                     )

association_table_project_to_issue = sqlalchemy.Table('project_to_issue', SqlAlchemyBase.metadata,
                                                      sqlalchemy.Column('issue_id', sqlalchemy.Integer,
                                                                        sqlalchemy.ForeignKey('issues.id')),
                                                      sqlalchemy.Column('project_id', sqlalchemy.Integer,
                                                                        sqlalchemy.ForeignKey('projects.id'))
                                                      )


class User(SqlAlchemyBase, UserMixin):
    """
    Implementation of user table

    id: it is a user unique id
    username: it is a user unique name
    hashed_password: it is a md5 hashed password
    created_date: it is a user profile creation date
    role: It is user role on website( Admin or just a user)

    To get user issues try User.issues
    """

    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    role = sqlalchemy.Column(sqlalchemy.String, default='User')

    issues = orm.relationship('Issue',
                              secondary=association_table_user_to_issue,
                              backref='assignees')
    projects = orm.relation('Project',
                            secondary=association_table_user_to_project,
                            backref='members')

    def __repr__(self):
        return f'username={self.username}; id={self.id}'

    def __str__(self):
        return self.__repr__()

    def check_password(self, password):
        # Here we checking if inputed password hash equal to hash in our database

        h = hashlib.new('md5', bytes(password, encoding='utf8'))
        return h.hexdigest() == self.hashed_password


class Project(SqlAlchemyBase):
    """
        Implementation of project table

        id: it is a project unique id
        project_name: it is a unique project name
        created_date: it is a project creation date
        issues: it is a relation with issues table

        To get specific user projects try Project.members
        """
    __tablename__ = 'projects'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)

    project_name = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)

    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    issues = orm.relation('Issue', secondary=association_table_project_to_issue, backref='project_issues')

    def __repr__(self):
        return f'Project name={self.project_name}; id={self.id}'

    def __str__(self):
        return self.__repr__()


class Issue(SqlAlchemyBase):
    """

    To get access specific user issues, try Issue.assignees
    To get access specific project issues try Issue.project_issues
    """
    __tablename__ = 'issues'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True, unique=True)

    tracking = sqlalchemy.Column(sqlalchemy.String, unique=True)
    priority = sqlalchemy.Column(sqlalchemy.String, index=True)
    state = sqlalchemy.Column(sqlalchemy.String)


    def __repr__(self):
        return f'Issue name={self.tracking}; id={self.id}'

    def __str__(self):
        return self.__repr__()
