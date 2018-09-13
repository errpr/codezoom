from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models.base import Base
from sqlalchemy.sql import func


class Run(Base):
    __tablename__ = 'runs'

    id = Column(Integer, primary_key=True)
    file_id = Column(String, nullable=False)
    output = Column(String)
    success_count = Column(Integer)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
    
    problem = relationship("Problem")

    def __repr__(self):
        return "<Run(output='{}')>".format(self.output)