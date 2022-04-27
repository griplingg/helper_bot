import datetime
import sqlalchemy
from .db_session_settings import SqlAlchemyBase
from sqlalchemy import orm


class Settings(SqlAlchemyBase):
    __tablename__ = 'settings'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    quote_author = sqlalchemy.Column(sqlalchemy.Boolean, nullable=True)


