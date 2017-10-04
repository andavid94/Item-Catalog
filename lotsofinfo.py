from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Items, User
import datetime

engine = create_engine('sqlite:///itemcatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create initial user data
User1 = User(
			name = "John Doe",
			email = "johndoe@gmail.com",
			picture = "https://pbs.twimg.com/profile_images/1237550450/mstom_400x400.jpg")
session.add(User1)
session.commit()


# Create category for areas in the Pacific Northwest
Category1 = Category(name = "Pacific Northwest", user_id = 1)
session.add(Category1)
session.commit()

Item1 = Items(
		name = "Seattle, WA",
		picture = "https://cdn.vox-cdn.com/uploads/chorus_image/image/53737065/eatersea0317_seattle_shutterstock.0.jpg",
		description = "Seattle is the largest city in the Pacific Northwest region of the United States. It is located in the U.S. state of Washington, about 108 miles (180 km) south of the American-Canadian border. ... Its official nickname is the Emerald City.",
		date = datetime.datetime.utcnow(),
		category_id = 1, 
		user_id = 1)
session.add(Item1)
session.commit()

Item2 = Items(
		name = "Portland, OR",
		picture = "https://www.visittheusa.com/sites/default/files/styles/hero_m_1300x700/public/images/hero_media_image/2016-11/Drone.__72%20DPI.jpg?itok=jhGikGPz",
		description = "This climate is ideal for growing roses, and Portland has been called the City of Roses for over a century. Keep Portland Weird is an unofficial slogan for the city.",
		date = datetime.datetime.utcnow(),
		category_id = 1,
		user_id = 1)
session.add(Item2)
session.commit()


# Create category for areas in California
Category2 = Category(name = "Southwest", user_id = 1)
session.add(Category2)
session.commit()

Item3 = Items(
		name = "San Diego",
		picture = "http://www.hotelpalomar-sandiego.com/images/tout/kimpton-hotel-palomar-san-diego-pier-b6a08a84.jpg",
		description = "Beautiful weather year-round, and an excellent place to vacation if you are a surfer or enjoy eating good mexican food.",
		date = datetime.datetime.utcnow(),
		category_id = 2,
		user_id = 1)
session.add(Item3)
session.commit()


# Create category for travel destinations
Category3 = Category(name = "Midwest", user_id = 1)
session.add(Category3)
session.commit()


# Create category for musical artists
Category4 = Category(name = "Hawaiian islands", user_id = 1)
session.add(Category4)
session.commit()

Category5 = Category(name = "Northeast", user_id = 1)
session.add(Category5)
session.commit()

Category6 = Category(name = "Southeast", user_id = 1)
session.add(Category6)
session.commit()

Category7 = Category(name = "Alaska", user_id = 1)
session.add(Category7)
session.commit()


print "added category and item information to database"
