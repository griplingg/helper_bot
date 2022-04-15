import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class Note(SqlAlchemyBase):
    __tablename__ = 'notes'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    def txt(self):
        return self.name
