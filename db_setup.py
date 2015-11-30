import os 
import sys
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
  __tablename__ = 'user'

  id = Column(Integer, primary_key=True)
  name = Column(String(250), nullable=False)
  email = Column(String(250), nullable=False)
  
class Movie(Base):
	__tablename__ = 'movie'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	trailer = Column(String, nullable=False)
	poster = Column(String, nullable=False)
	genre = Column(String(10))
	info = Column(String)
	user_id = Column(Integer, ForeignKey('user.id'))

	user = relationship(User)

	@property  
	def serialize(self):
		return {
			'name': self.name,
			'genre': self.genre,
			'id': self.id,
		}


engine = create_engine('postgres://csajqmbvzicfmy:Ziw2YSvCtPWiYebo6GkSqnEpZN@ec2-54-197-253-142.compute-1.amazonaws.com:5432/d4jhvu06cnvfpe')
# engine = create_engine('sqlite:///movies.db')

Base.metadata.create_all(engine)

