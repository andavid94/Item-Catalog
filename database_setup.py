import datetime
from sqlalchemy import Column, ForeignKey, Integer, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = False)
	email = Column(String(250))
	picture = Column(String(250))


class Region(Base):
	__tablename__ = 'region'

	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = False)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	cities = relationship('Cities')


	@property
	def serialize(self):
		# Return object data in easily serializable format
		return {
			'name': self.name,
			'id': self.id,
		}


class Cities(Base):
	__tablename__ = 'cities'

	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = False)
	description = Column(String(250))
	picture = Column(String(250))
	date = Column(DateTime, nullable = False)
	region_id = Column(Integer, ForeignKey('region.id'))
	region = relationship(Region)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		# Return object data in easily serializeable format
		return {
			'name': self.name,
			'description': self.description,
			'picture': self.picture,
			'id': self.id,
			'region': self.region,
		}


engine = create_engine('sqlite:///travelDocument.db')


Base.metadata.create_all(engine)
