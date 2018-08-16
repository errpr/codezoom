from sqlalchemy import Column, Integer, String
from models.base import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    pw_hash = Column(String)

    def __repr__(self):
        return "<User(name='{}', fullname='{}', pw_hash='{}')>".format(self.name, self.fullname, self.password)