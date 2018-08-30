from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models.base import Base
from models.test import Test
from sqlalchemy.sql import func

class Problem(Base):
    __tablename__ = 'problems'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="problems")
    tests = relationship("Test", order_by=Test.id, back_populates="problem")

    def __repr__(self):
        return "<Problem(title='{}', user_id='{}')>".format(self.title, self.user_id)