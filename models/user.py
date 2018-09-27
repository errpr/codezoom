from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from models.base import Base
from models.room import Room
from models.run import Run
from models.problem import Problem
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    fullname = Column(String)
    pw_hash = Column(String, nullable=False)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    rooms = relationship("Room", backref="owner")
    runs = relationship("Run", backref="user")
    problems = relationship("Problem", backref="user")

    def __repr__(self):
        return "<User(name='{}', fullname='{}', pw_hash='{}')>".format(self.name, self.fullname, self.password)