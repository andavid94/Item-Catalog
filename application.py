from flask import Flask, render_template, request, redirect, url_for
from flask import Flask, jsonify, flash, session as login_session
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Region, Cities, User
import random, string, os, datetime
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from login_decorator import login_required


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///travelDocument.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()


#Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE = state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(data['email'])
    if not user_id:
    	user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output



# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result.status == 200:
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = redirect(url_for('showCatalog'))
        response.headers['Content-Type'] = 'application/json'
        flash("you have successfully logged out")
        return response
    else: 
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


def createUser(login_session):
	newUser = User(name = login_session['username'], email = login_session[
				'email'], picture = login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email = login_session['email']).one()
	return user.id


def getUserInfo(user_id):
	user = session.query(User).filter_by(id = user_id).one()
	return user


def getUserID(email):
	try:
		user = session.query(User).filter_by(email = email).one()
		return user.id
	except:
		return None



# JSON APIs to view Catalog information
@app.route('/catalog/JSON')
@app.route('/catalog/regions/JSON')
def showCatalogJSON():
	regions = session.query(Region).all()
	return jsonify(regions = [region.serialize for region in regions])

@app.route('/catalog/cities/JSON')
def citiesJson():
	cities = session.query(Cities).all()
	return jsonify(cities = [city.serialize for city in cities])

@app.route('/catalog/<path:region_name>/cities/JSON')
def regionCiiesJSON(region_name):
	region = session.query(Region).filter_by(name = region_name).one()
	cities = session.query(Cities).filter_by(region = region_name).all()
	return jsonify(cities = [city.serialize for city in cities])

@app.route('/catalog/<path:region_name>/<path:city_name>/JSON')
def CityJSON(region_name, city_name):
	city = session.query(Cities).filter_by(name = city_name).first()
	return jsonify(city = [city.serialize])


# Flask routing
# Default/Home Page
@app.route('/')
@app.route('/catalog/')
def showCatalog():
	regions = session.query(Region).order_by(asc(Region.name))
	cities = session.query(Cities).order_by(desc(Cities.date))
	return render_template(
		'catalog.html', regions = regions, cities = cities)



# Show cities in given region
@app.route('/catalog/<path:region_name>/cities/')
def showRegion(region_name):
	regions = session.query(Region).order_by(asc(Region.name))
	region = session.query(Region).filter_by(name = region_name).one()
	creator = getUserInfo(region.user_id)
	cities = session.query(Cities).filter_by(
			region = region).all()
	print cities
	if 'username' not in login_session or creator.id != login_session.get('user_id'):
		return render_template('publicCities.html', region = region.name,
								regions = regions, cities = cities)
	else:
		user = getUserInfo(login_session['user_id'])
		return render_template('cities.html', region = region.name,
								regions = regions, cities = cities, user = user)


# Show a particular city
@app.route('/catalog/<path:region_name>/<path:city_name>/')
def showCity(region_name, city_name):
	regions = session.query(Region).order_by(asc(Region.name))
	city = session.query(Cities).filter_by(name = city_name).one()
	creator = getUserInfo(city.user_id)
	if 'username' not in login_session or creator.id != login_session.get('user_id'):
		return render_template('publiccitydetail.html', region = region_name,
								regions = regions, city = city)
	else:
		return render_template('citydetail.html', region = region_name,
								regions = regions, city = city, creator = creator)


# Create a new City
@app.route('/catalog/add/', methods = ['GET', 'POST'])
def addCity():
	regions = session.query(Region).all()
	if request.method == 'POST':
		newCity = Cities(name = request.form['name'], picture = request.form['picture'],
			description = request.form['description'], date = datetime.datetime.utcnow(), 
			region = session.query(Region).
			filter_by(name = request.form['region']).one(), user_id = login_session.get('user_id'))
		session.add(newCity)
		session.commit()
		flash('New City has successfully been created')
		return redirect(url_for('showCatalog'))
	else: 
		return render_template('addCity.html', regions = regions)


# Edit an existing City
@app.route('/catalog/<path:region_name>/<path:city_name>/edit', methods=['GET', 'POST'])
def editCity(region_name, city_name):
	regions = session.query(Region).all()
	editedCity = session.query(Cities).filter_by(name = city_name).one()
	creator = getUserInfo(editedCity.user_id)
	user = getUserInfo(login_session.get('user_id'))
	if login_session.get('user_id') != creator.id:
		flash('You cannot edit this city since you are not the creator')
		return redirect(url_for('showCatalog'))
	if request.method == 'POST':
		if request.form['name']:
			editedCity.name = request.form['name']
		if request.form['picture']:
			editedCity.picture = request.form['picture']
		if request.form['description']:
			editedCity.description = request.form['description']
		if request.form['region']:
			region = session.query(Region).filter_by(name = 
					request.form['region']).one()
			editedCity.region = region 
		time = datetime.datetime.utcnow()
		editedCity.date = time
		session.add(editedCity)
		session.commit()
		flash('Your city has been successfully edited.')
		return redirect(url_for('showRegion', 
				region_name = editedCity.region.name))
	else:
		return render_template('editcity.html', city = editedCity,
								regions = regions)


# Delete an existing City
@app.route('/catalog/<path:region_name>/<path:city_name>/delete', methods=['GET', 'POST'])
def deleteCity(region_name, city_name):
	cityToDelete = session.query(Cities).filter_by(name = city_name).one()
	regions = session.query(Region).all()
	region = session.query(Region).filter_by(name = region_name).one()
	creator = getUserInfo(cityToDelete.user_id)
	user = getUserInfo(login_session.get('user_id'))
	if login_session.get('user_id') != creator.id:
		flash('You cannot delete this city since you are not the creator')
		return redirect(url_for(showCatalog))
	if request.method == 'POST':
		session.delete(cityToDelete)
		session.commit()
		flash('Your city has been successfully deleted')
		return redirect(url_for('showRegion', region_name = region.name))
	else: 
		return render_template('deletecity.html', city = cityToDelete)




if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)

