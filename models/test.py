from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models.base import Base
from sqlalchemy.sql import func


class Test(Base):
    __tablename__ = 'tests'

    id = Column(Integer, primary_key=True)
    input = Column(String, nullable=False)
    output = Column(String, nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
    
    problem = relationship("Problem", back_populates="tests")

    def __repr__(self):
        return "<Problem(title='{}', user_id='{}')>".format(self.title, self.user_id)