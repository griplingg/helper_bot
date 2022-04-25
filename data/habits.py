import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Habit(SqlAlchemyBase):
    __tablename__ = 'habits'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    habit = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    question = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    time = sqlalchemy.Column(sqlalchemy.Time, nullable=True)
    tracking = orm.relation("Tracking", back_populates='habit')

    def txt(self):
        return self.habit
