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


# Create category for tennis players
Category1 = Category(name = "Tennis Players", user_id = 1)
session.add(Category1)
session.commit()

Item1 = Items(
		name = "Roger Federer",
		description = "Arguably the greatest tennis player of all time.",
		date = datetime.datetime.utcnow(),
		category_id = 1, 
		user_id = 1)
session.add(Item1)
session.commit()

Item2 = Items(
		name = "Rafael Nadal",
		description = "World renowned spanish player",
		date = datetime.datetime.utcnow(),
		category_id = 1,
		user_id = 1)
session.add(Item2)
session.commit()


# Create category for foods
Category2 = Category(name = "Foods", user_id = 1)
session.add(Category2)
session.commit()

Item3 = Items(
		name = "Sushi",
		description = "Raw fish paired with slightly salted rice",
		date = datetime.datetime.utcnow(),
		category_id = 2,
		user_id = 1)
session.add(Item3)
session.commit()


# Create category for travel destinations
Category3 = Category(name = "Destinations", user_id = 1)
session.add(Category3)
session.commit()

Item4 = Items(
		name = "New Zealand",
		description = "Filming location for the Lord of the Rings",
		date = datetime.datetime.utcnow(),
		category_id = 3,
		user_id = 1)
session.add(Item4)
session.commit()


# Create category for musical artists
Category4 = Category(name = "Musical Artists", user_id = 1)
session.add(Category4)
session.commit()

Item5 = Items(
		name = "Coldplay",
		description = "Soft rock band",
		date = datetime.datetime.utcnow(),
		category_id = 4,
		user_id = 1)
session.add(Item5)
session.commit()


print "added category and item information to database"










