from typing import List, NamedTuple, Optional
import functools
import logging as log
import uuid

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKeyConstraint, or_, ForeignKey, distinct
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class NumberRoomMap(Base):
    __tablename__ = "number_room_map"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    number = Column(Text, index=True, nullable=False)
    room = Column(Text, index=True, nullable=False)
    number_name = Column(Text)
    room_name = Column(Text)

    __table_args__ = (UniqueConstraint("number"),)


def sessionized(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        kwargs["session"] = self.Session(expire_on_commit=False)
        return f(self, *args, **kwargs)
        kwargs["session"].commit()

    return wrapped


class Database:
    db: Engine

    def __init__(self, db: Engine) -> None:
        self.db = db
        Base.metadata.bind = db
        Base.metadata.create_all(db)
        self.Session = sessionmaker(bind=self.db)

    @sessionized
    def map(self, number, number_name, room, room_name, session=None):
        row = NumberRoomMap(number=str(number), number_name=str(number_name), room=str(room), room_name=str(room_name))
        session.add(row)
        session.commit()

    @sessionized
    def unmap(self, number, room, session=None):
        rows = session.query(NumberRoomMap).filter_by(number=str(number), room=str(room))
        if not rows:
            return False
        session.delete(rows[0])
        session.commit()
        return True

    @sessionized
    def get(self, number=None, room=None, session=None):
        kwargs = {}

        if number:
            kwargs["number"] = str(number)
        if room:
            kwargs["room"] = str(room)

        if not kwargs:
            return []

        return session.query(NumberRoomMap).filter_by(**kwargs).all()
