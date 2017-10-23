from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Region, Cities, User
import datetime

engine = create_engine('sqlite:///travelDocument.db')
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


# Create region for cities in the Pacific Northwest
Region1 = Region(name = "Pacific Northwest", user_id = 1)
session.add(Region1)
session.commit()

City1 = Cities(
		name = "Seattle, WA",
		picture = "https://cdn.vox-cdn.com/uploads/chorus_image/image/53737065/eatersea0317_seattle_shutterstock.0.jpg",
		description = "Seattle is the largest city in the Pacific Northwest region of the United States. It is located in the U.S. state of Washington, about 108 miles (180 km) south of the American-Canadian border. ... Its official nickname is the Emerald City.",
		date = datetime.datetime.utcnow(),
		region_id = 1, 
		user_id = 1)
session.add(City1)
session.commit()


# Create region for cities in California
Region2 = Region(name = "Southwest", user_id = 1)
session.add(Region2)
session.commit()

City2 = Cities(
		name = "San Diego, CA",
		picture = "http://www.hotelpalomar-sandiego.com/images/tout/kimpton-hotel-palomar-san-diego-pier-b6a08a84.jpg",
		description = "Beautiful weather year-round, and an excellent place to vacation if you are a surfer or enjoy eating good mexican food.",
		date = datetime.datetime.utcnow(),
		region_id = 2,
		user_id = 1)
session.add(City2)
session.commit()


# Create region for cities in the midwest
Region3 = Region(name = "Midwest", user_id = 1)
session.add(Region3)
session.commit()


Region4 = Region(name = "Hawaiian islands", user_id = 1)
session.add(Region4)
session.commit()

City3 = Cities(
	name = "Kailua, HI",
	picture = "http://images.kuoni.co.uk/73/hawaii-40591419-1483623557-ImageGalleryLightboxLarge.jpg",
	description = "Kailua is a place of much natural beauty. The most significant features of Kailua are the bay, the mountains, and the wetlands.  Kailua Bay is a magnificent place symbolizing the regional quality of the community.  Kailua Beach and nearby Lanikai have been on the Worlds Best Beach lists by several publishers for many years.",
	date = datetime.datetime.utcnow(),
	region_id = 4,
	user_id = 1)
session.add(City3)
session.commit()


Region5 = Region(name = "Northeast", user_id = 1)
session.add(Region5)
session.commit()


Region6 = Region(name = "Southeast", user_id = 1)
session.add(Region6)
session.commit()


Region7 = Region(name = "Alaska", user_id = 1)
session.add(Region7)
session.commit()


print "added region and city information to database"
