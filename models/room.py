from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from models.base import Base
from models.problem import Problem
from sqlalchemy.sql import func

class RoomProblem(Base):
    __tablename__ = 'room_problems'
    room_id = Column(String, ForeignKey('rooms.id'), primary_key=True)
    problem_id = Column(Integer, ForeignKey('problems.id'), primary_key=True)
    order_id = Column(Integer)

class Room(Base):
    __tablename__ = 'rooms'

    id = Column(String, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="rooms")
    problems = relationship("RoomProblem", order_by=RoomProblem.order_id)

    def __repr__(self):
        return "<Room(title='{}', user_id='{}')>".format(self.title, self.user_id)