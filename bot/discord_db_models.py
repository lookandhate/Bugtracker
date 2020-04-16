"""
Implementation of discord database
"""

import datetime
import sqlalchemy
from data import db_session
from data.db_session import SqlAlchemyBase


class DiscordUser(SqlAlchemyBase):
    """
    This is a table where we will collect user id and their api key on site
    """
    __tablename__ = 'discord'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    discord_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    site_api_key = sqlalchemy.Column(sqlalchemy.String)

    def update_api_key(self, discord_id, new_api_key):
        session = db_session.create_session()
        # Get the user object
        user = session.query(DiscordUser).filter(DiscordUser.discord_id == discord_id).first()
        user.site_api_key = new_api_key
        session.merge(user)
        session.commit()

    def get_api_key(self, discord_id):
        session = db_session.create_session()
        return session.query(DiscordUser.site_api_key).filter(DiscordUser.discord_id == discord_id).firsr()
