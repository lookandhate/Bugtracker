import datetime
import sqlalchemy
import hashlib

from typing import Iterable

from .db_session import SqlAlchemyBase, create_session
from sqlalchemy import orm, select, insert
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin

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
                                                     sqlalchemy.Column('project_role', sqlalchemy.String),
                                                     sqlalchemy.Column('date_of_add', sqlalchemy.DateTime,
                                                                       default=datetime.datetime.now)
                                                     )

association_table_project_to_issue = sqlalchemy.Table('project_to_issue', SqlAlchemyBase.metadata,
                                                      sqlalchemy.Column('issue_id', sqlalchemy.Integer,
                                                                        sqlalchemy.ForeignKey('issues.id')),
                                                      sqlalchemy.Column('project_id', sqlalchemy.Integer,
                                                                        sqlalchemy.ForeignKey('projects.id'))
                                                      )
association_table_subsystems_to_project = sqlalchemy.Table('subsystems_to_project', SqlAlchemyBase.metadata,
                                                           sqlalchemy.Column('project_id', sqlalchemy.Integer,
                                                                             sqlalchemy.ForeignKey('projects.id')),
                                                           sqlalchemy.Column('subsystem', sqlalchemy.String)
                                                           )
association_table_file_to_issue = sqlalchemy.Table('file_to_issue', SqlAlchemyBase.metadata,
                                                   sqlalchemy.Column('issue_id', sqlalchemy.Integer,
                                                                     sqlalchemy.ForeignKey('issues.id')),
                                                   sqlalchemy.Column('file_path', sqlalchemy.String)
                                                   )

association_table_priority_to_project = sqlalchemy.Table('priority_to_project', SqlAlchemyBase.metadata,
                                                         sqlalchemy.Column('project_id', sqlalchemy.Integer,
                                                                           sqlalchemy.ForeignKey('projects.id')),
                                                         sqlalchemy.Column('priority', sqlalchemy.String)
                                                         )


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
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

    reg_ip = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    last_ip = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    role = sqlalchemy.Column(sqlalchemy.String, default='User')

    issues = orm.relation('Issue',
                          secondary=association_table_user_to_issue,
                          backref='assignees')
    projects = orm.relation('Project',
                            secondary=association_table_user_to_project,
                            backref='members')

    def __repr__(self):
        return f'username={self.username}; id={self.id};role={self.role};\nprojects {self.projects}\nissues:{self.issues}'

    def __str__(self):
        return self.__repr__()

    def check_password(self, password):
        # Here we checking if inputed password hash equal to hash in our database

        h = hashlib.new('md5', bytes(password, encoding='utf8'))
        return h.hexdigest() == self.hashed_password

    def project_role(self, project_id):
        '''

        :param project_id: ID of the project from which we want the user role
        :return: None if user not in that project
        '''

        session = create_session()
        result = session.execute(
            select([association_table_user_to_project.c.project_role]).where(
                association_table_user_to_project.c.member_id == self.id).where(
                association_table_user_to_project.c.project_id == project_id)
        ).fetchone()['project_role']
        session.close()
        return result

    def project_date_of_add(self, project_id):
        session = create_session()
        result = session.execute(
            select([association_table_user_to_project.c.date_of_add]).where(
                association_table_user_to_project.c.member_id == self.id).where(
                association_table_user_to_project.c.project_id == project_id)
        ).fetchone()['date_of_add']

        return result

    @property
    def is_admin(self):
        return self.role == 'Admin'


class Project(SqlAlchemyBase, SerializerMixin):
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

    description = sqlalchemy.Column(sqlalchemy.String(256))
    short_project_tag = sqlalchemy.Column(sqlalchemy.String, unique=True)
    issues = orm.relation('Issue', secondary=association_table_project_to_issue, backref='project')

    def __repr__(self):
        return f'Project name= {self.project_name}; id= {self.id}; root= {self.get_root().username}\ndesc: {self.description}' \
               f'\nmembers: {len(self.members)}\nissues: {len(self.issues)}'

    def __str__(self):
        return self.__repr__()

    def get_project_subsystems(self):
        session = create_session()
        result = session.execute(
            select([association_table_subsystems_to_project.c.subsystem]).where(
                association_table_subsystems_to_project.c.project_id == self.id
            )
        ).fetchall()
        session.close()
        return result

    def add_project_subsystems(self, subsystems: Iterable):
        session = create_session()
        for subsystem in subsystems:
            session.execute(association_table_subsystems_to_project.insert().values(self.id, subsystem))
        session.commit()
        session.close()

    def get_project_priorities(self):
        session = create_session()
        result = session.execute(
            select([association_table_priority_to_project.c.priority]).where(
                association_table_priority_to_project.c.project_id == self.id
            )
        ).fetchall()
        session.close()
        return result

    def add_project_priorities(self, id: int, priorities: Iterable):
        session = create_session()
        for priority in priorities:
            session.execute(association_table_priority_to_project.insert(),
                            {'project_id': id, 'priority': priority})
        session.commit()
        session.close()

    def get_root(self):
        """

        :return: Return User object of project root (i.e creator)
        """
        session = create_session()
        member_id = session.execute(
            select([association_table_user_to_project.c.member_id]).where(
                association_table_user_to_project.c.project_id == self.id
            ).where(
                association_table_user_to_project.c.project_role == 'root'
            )
        ).fetchone()
        member_id = member_id['member_id']
        user = session.query(User).filter(User.id == member_id).first()
        session.close()
        return user


class Issue(SqlAlchemyBase, SerializerMixin):
    """

    To get access specific user issues, try Issue.assignees
    To get access specific project issues try Issue.project
    """
    __tablename__ = 'issues'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True, unique=True)

    tracking = sqlalchemy.Column(sqlalchemy.String, unique=True)
    priority = sqlalchemy.Column(sqlalchemy.String, index=True)
    state = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
    steps_to_reproduce = sqlalchemy.Column(sqlalchemy.String)
    summary = sqlalchemy.Column(sqlalchemy.String)
    date_of_creation = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return f'Issue name={self.tracking}; id={self.id}\ndesc: {self.description}'

    def __str__(self):
        return self.__repr__()

    def get_attachments(self):
        """
        :return: list of attachments path
        """
        session = create_session()
        result = session.execute(
            select([association_table_file_to_issue.c.file_path]).where(
                association_table_file_to_issue.c.issue_id == self.id
            )
        ).fetchall()['file_path']
        session.close()
        return result
