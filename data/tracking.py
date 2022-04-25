import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Tracking(SqlAlchemyBase):
    __tablename__ = 'tracking'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    done = sqlalchemy.Column(sqlalchemy.BOOLEAN, nullable=True)
    habit_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("habits.id"))
    habit = orm.relation('Habit')

