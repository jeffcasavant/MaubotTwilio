import functools
import uuid

from sqlalchemy import Column, Text, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class NumberRoomMap(Base):
    __tablename__ = "number_room_map"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    number = Column(Text, index=True, nullable=False)
    room = Column(Text, index=True, nullable=False)
    name = Column(Text)

    __table_args__ = (UniqueConstraint("number"),)


def sessionized(func):
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        kwargs["session"] = self.Session(expire_on_commit=False)
        resp = func(self, *args, **kwargs)
        kwargs["session"].commit()
        return resp

    return wrapped


class Database:
    db: Engine

    def __init__(self, logger, db: Engine) -> None:
        self.logger = logger
        self.logger.debug("Init database")
        self.db = db
        Base.metadata.bind = db
        Base.metadata.create_all(db)
        self.Session = sessionmaker(bind=self.db)

    @sessionized
    def map(self, number, name, room, session=None):
        row = NumberRoomMap(number=str(number), name=str(name), room=str(room))
        session.add(row)
        session.commit()

    @sessionized
    def unmap(self, identifier, session=None):
        session.query(NumberRoomMap).filter(
            or_(NumberRoomMap.name == identifier, NumberRoomMap.number == identifier)
        ).delete()
        session.commit()

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

    @sessionized
    def list(self, room=None, session=None):
        return session.query(NumberRoomMap).filter_by(room=str(room)).all()
