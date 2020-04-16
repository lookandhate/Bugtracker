import datetime
import sqlalchemy
import hashlib

from typing import Iterable, Optional

from .db_session import SqlAlchemyBase, create_session
from src.misc_funcs import generate_random_string

from sqlalchemy import orm, select
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
    API_KEY = sqlalchemy.Column(sqlalchemy.String(24))

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

    def check_password(self, password: str) -> bool:
        """
        Check if hash of given password equal to hash of password in database
        :param password: String with password
        :return: True if hashes are equal, otherwise False
        """

        hash_of_given_password = hashlib.new('md5', bytes(password, encoding='utf8'))
        return hash_of_given_password.hexdigest() == self.hashed_password

    def project_role(self, project_id: int) -> Optional[str]:
        """
        :param project_id: Project.id of the Project from which we want the user role
        :return: String if User in project members and None if user not in that project
        """

        session = create_session()
        result = session.execute(
            select([association_table_user_to_project.c.project_role]).where(
                association_table_user_to_project.c.member_id == self.id).where(
                association_table_user_to_project.c.project_id == project_id)
        ).fetchone()
        session.close()
        return result[0]

    def change_project_role(self, project_id: int, role: str) -> None:
        """
        Updates User role in Project
        :param project_id: Project.id of Project in what we want to update user Role
        :param role: new user role
        :return: None
        """

        session = create_session()
        session.execute(association_table_user_to_project.update().where(
            association_table_user_to_project.c.project_id == project_id).where(
            association_table_user_to_project.c.member_id == self.id).values(
            project_role=role))
        session.merge(self)
        session.commit()

    def project_date_of_add(self, project_id: int) -> datetime.datetime:
        """
        :param project_id: Project.id of Project
        :return: User join time to Project
        """

        session = create_session()
        result = session.execute(
            select([association_table_user_to_project.c.date_of_add]).where(
                association_table_user_to_project.c.member_id == self.id).where(
                association_table_user_to_project.c.project_id == project_id)
        ).fetchone()['date_of_add']

        return result

    def count_of_issues_total(self, project_id: int) -> int:
        """

        :param project_id: Project.id of Project in what we want to count user issues
        :return: Amount of user assignees in Project
        """
        session = create_session()
        temp = session.query(Issue).filter(Issue.project_id == project_id).filter(Issue.assignees.contains(self)).all()
        return len(temp)

    def regenerate_API_key(self) -> None:
        """
        Regenerates User API key with 24-length string
        :return: None
        """
        session = create_session()
        new_key = generate_random_string(24)
        # Check if there is any user with exact same API key as just generated
        if new_key not in session.query(User.API_KEY).all():
            self.API_KEY = new_key
            session.merge(self)
            session.commit()
        else:
            while new_key in session.query(User.API_KEY).all():
                new_key = generate_random_string(24)
            self.API_KEY = new_key
            session.merge(self)
            session.commit()

    @property
    def is_admin(self) -> bool:
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

    def get_project_subsystems(self) -> Optional[Iterable[str]]:
        """
        :return: Either iterable object that contains strings of Project subsystems
        """

        session = create_session()
        result = session.execute(
            select([association_table_subsystems_to_project.c.subsystem]).where(
                association_table_subsystems_to_project.c.project_id == self.id
            )
        ).fetchall()
        session.close()
        return result

    def add_project_subsystems(self, subsystems: Iterable[str]) -> None:
        """
        Add subsystems to Project
        :param subsystems: Iterable object that contains subsystems
        :return: None
        """

        session = create_session()
        for subsystem in subsystems:
            session.execute(association_table_subsystems_to_project.insert().values(self.id, subsystem))
        session.commit()
        session.close()

    def get_project_priorities(self) -> Optional[Iterable[str]]:
        """
        :return: Iterable object that contains all strings of project priorities
        """
        session = create_session()
        priorities_list = session.execute(
            select([association_table_priority_to_project.c.priority]).where(
                association_table_priority_to_project.c.project_id == self.id
            )
        ).fetchall()
        session.close()
        return priorities_list

    def add_project_priorities(self, priorities: Iterable) -> None:
        """
        Add priorities to Project
        :param priorities: Iterable object that contains Priorities
        :return: None
        """

        session = create_session()
        for priority in priorities:
            session.execute(association_table_priority_to_project.insert(),
                            {'project_id': self.id, 'priority': priority})
        session.commit()
        session.close()

    def get_root(self) -> Optional[User]:
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

    # API METHODS BLOCK BELOW
    def subsystems(self) -> Optional[Iterable[str]]:
        """
        USE ONLY FOR API
        Proxy method for API
        :return: List of project subsystems or None
        """

        return self.get_project_subsystems()

    def priorities(self) -> Optional[Iterable[str]]:
        """
        USE ONLY FOR API
        Proxy method for API
        :return: List of project priorities or None
        """

        return self.get_project_priorities()

    def root(self) -> Optional[str]:
        """
        USE ONLY FOR API
        Proxy method for API
        :return: Return username of User-project root (i.e creator)
        """

        return self.get_root().username if self.get_root() else None
    # API METHODS BLOCK ABOVE


class Issue(SqlAlchemyBase, SerializerMixin):
    """
    Implementation of issues table in database
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

    project_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('projects.id'))

    def __repr__(self):
        return f'Issue name={self.tracking}; id={self.id}\ndesc: {self.description}'

    def __str__(self):
        return self.__repr__()

    def get_attachments(self) -> Optional[Iterable[str]]:
        """
        :return: list of attachments path
        """
        session = create_session()
        attachments_list = session.execute(
            select([association_table_file_to_issue.c.file_path]).where(
                association_table_file_to_issue.c.issue_id == self.id
            )
        ).fetchall()['file_path']
        session.close()
        return attachments_list

    # API METHODS BLOCK BELOW
    def project_name(self):
        return self.project.project_name

    def assign_on(self):
        return self.assignees.username
    # API METHOD ABOVE
