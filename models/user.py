from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from models.base import Base
from models.problem import Problem
from models.room import Room
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    fullname = Column(String)
    pw_hash = Column(String, nullable=False)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    rooms = relationship("Room", back_populates="owner")
    problems = relationship("Problem", order_by=Problem.id, back_populates="user")
    runs = relationship("Runs", back_populates="user")

    def __repr__(self):
        return "<User(name='{}', fullname='{}', pw_hash='{}')>".format(self.name, self.fullname, self.password)