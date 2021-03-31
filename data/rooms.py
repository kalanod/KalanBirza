import datetime
import sqlalchemy
from sqlalchemy import update
from data.db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Rooms(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'rooms'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    creator = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    players = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    status = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return f'<Room> {self.id} {self.title} creator: {self.creator}'