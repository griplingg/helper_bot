import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class Citat(SqlAlchemyBase):
    __tablename__ = 'citat'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    #author = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    def txt(self):
        return self.name
