from flask import Flask, render_template, request, redirect, url_for
from flask import Flask, jsonify, flash, session as login_session
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Items, User
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
engine = create_engine('sqlite:///itemcatalog.db')
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
    #response = h.request(url, 'GET')[1]
    #str_response = response.decode('utf-8')
    #result = json.loads(str_response)
    # If there was an error in the access token info, abort.
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
def allItemsJSON():
	categories = session.query(Category).all()
	category_dict = [c.serialize for c in categories]
	for c in range(len(category_dict)):
		items = [i.serialize for i in session.query(Items)
				.filter_by(category_id = category_dict[c]['id']).all()]
		if items:
			category_dict[c]['Item'] = items
	return jsonify(Category = category_dict)

@app.route('/catalog/categories/JSON')
def categoriesJSON():
	categories = session.query(Category).all()
	return jsonify(categories = [c.serialize for c in categories])

@app.route('/catalog/items/JSON')
def itemsJson():
	items = session.query(Items).all()
	return jsonify(items = [i.serialize for i in items])

@app.route('/catalog/<path:category_name>/items/JSON')
def categoryItemsJSON(category_name):
	category = session.query(Category).filter_by(name = category_name).one()
	items = session.query(Items).filter_by(category = category).all()
	return jsonify(items = [i.serialize for i in items])

@app.route('/catalog/<path:category_name>/<pathLitem_name>/JSON')
def ItemJSON(category_name, item_name):
	category = session.query(Category).filter_by(name = category_name).one()
	item = session.query(Items).filter_by(name = item_name,
										category = category).one()
	return jsonify(item = [item.serialize])


# Flask routing
# Default/Home Page
@app.route('/')
@app.route('/catalog/')
def showCatalog():
	categories = session.query(Category).order_by(asc(Category.name))
	items = session.query(Items).order_by(asc(Items.date))
	return render_template(
		'catalog.html', categories = categories, items = items)



# Show items in given category
@app.route('/catalog/<path:category_name>/items/')
def showCategory(category_name):
	categories = session.query(Category).order_by(asc(Category.name))
	category = session.query(Category).filter_by(name = category_name).one()
	creator = getUserInfo(category.user_id)
	items = session.query(Items).filter_by(
			category = category).all()
	print items
	#count = session.query(Items).filter_by(category = category).count()
	if 'username' not in login_session or creator.id != login_session.get('user_id'):
		return render_template('publicItems.html', category = category.name,
								categories = categories, items = items)
	else:
		user = getUserInfo(login_session['user_id'])
		return render_template('items.html', category = category.name,
								categories = categories, items = items, user = user)


# Show a particular item
@app.route('/catalog/<path:category_name>/<path:item_name>/')
def showItem(category_name, item_name):
	categories = session.query(Category).order_by(asc(Category.name))
	item = session.query(Items).filter_by(name = item_name).one()
	creator = getUserInfo(item.user_id)
	if 'username' not in login_session or creator.id != login_session.get('user_id'):
		return render_template('publicitemdetail.html', category = category_name,
								categories = categories, item = item)
	else:
		return render_template('itemdetail.html', category = category_name,
								categories = categories, item = item, creator = creator)


# Create new category
@app.route('/catalog/newcategory/', methods = ['GET', 'POST'])
def addCategory():
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == 'POST':
		newCategory = Category(
			name = request.form['name'], user_id = login_session.get('user_id'))
		session.add(newCategory)
		session.commit()
		flash('New Category Successfully Created')
		return redirect(url_for('showCatalog'))
	else:
		return render_template('addcategory.html')


# Edit an existing category
@app.route('/catalog/<path:category_name>/edit/', methods = ['GET', 'POST'])
def editCategory(category_name):
	category = session.query(Category).filter_by(name = category_name).one()
	editedCategory = session.query(Category).filter_by(name = category_name).one()
	creator = getUserInfo(editedCategory.user_id)
	user = getUserInfo(login_session).get('user_id')

	if login_session.get('user_id') != creator.id:
		flash('You are unable to edit this Category since you are not the creator')
		return redirect(url_for('showCatalog'))
	if request.method == 'POST':
		if request.form['name']:
			editedCategory.name = request.form['name']
		session.add(editedCategory)
		session.commit()
		flash('Category has been successfully edited.')
		return redirect(url_for('showCatalog'))
	else:
		return render_template('editcategory.html', categories = editedCategory,
								category = category)


# Delete an existing category
@app.route('/catalog/<path:category_name>/delete', methods = ['GET', 'POST'])
def deleteCategory(category_name):
	categoryToDelete = session.query(
			Category).filter_by(name = category_name).one()
	creator = getUserInfo(categoryToDelete.user_id)
	user = getUserInfo(login_session.get('user_id'))

	if login_session.get('user_id') != creator.id:
		flash('You cannot delete this Cateogry since you are not the creator')
		return redirect(url_for('showCatalog'))
	if request.method == 'POST':
		session.delete(categoryToDelete)
		session.commit()
		flash ('Category has been successfully deleted.')
		return redirect(url_for('showCatalog'))
	else:
		return render_template('deletecategory.html', category = categoryToDelete)


# Create a new Item
@app.route('/catalog/add/', methods = ['GET', 'POST'])
def addItem():
	categories = session.query(Category).all()
	if request.method == 'POST':
		newItem = Items(name = request.form['name'], 
			description = request.form['description'], date = datetime.datetime.now(), 
			category = session.query(Category).
			filter_by(name = request.form['category']).one(), user_id = login_session.get('user_id'))
		session.add(newItem)
		session.commit()
		flash('New Item has successfully been created')
		return redirect(url_for('showCatalog'))
	else: 
		return render_template('addItem.html', categories = categories)


# Edit an existing Item
@app.route('/catalog/<path:category_name>/<path:item_name>/edit', methods=['GET', 'POST'])
def editItem(category_name, item_name):
	categories = session.query(Category).all()
	editedItem = session.query(Items).filter_by(name = item_name).one()
	creator = getUserInfo(editedItem.user_id)
	user = getUserInfo(login_session.get('user_info'))
	if login_session.get('user_info') != creator.id:
		flash('You cannot edit this item since you are not the creator')
		return redirect(url_for('showCatalog'))
	if request.method == 'POST':
		if request.form['name']:
			editedItem.name = request.form['name']
		if request.form['description']:
			editedItem.description = request.form['description']
		if request.form['category']:
			category = session.query(Category).filter_by(name = 
					request.form['category']).one()
			editedItem.category = category 
		time = datetime.datetime.utcnow()
		editedItem.date = time
		session.add(editedItem)
		session.commit()
		flash('Item has been successfully edited.')
		return redirect(url_for('showCategory', 
				category_name = editedItem.category.name))
	else:
		return render_template('edititem.html', item = editedItem,
								categories = categories)


# Delete an existing Item
@app.route('/catalog/<path:category_name>/<path:item_name>/delete', methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
	itemToDelete = session.query(Items).filter_by(name = item_name).one()
	categories = session.query(Category).all()
	category = session.query(Category).filter_by(name = category_name).one()
	creator = getUserInfo(itemToDelete.user_id)
	user = getUserInfo(login_session.get('user_info'))
	if login_session.get('user_info') != creator.id:
		flash('You cannot delete this item since you are not the creator')
		return redirect(url_for(showCatalog))
	if request.method == 'POST':
		session.delete(itemToDelete)
		session.commit()
		flash('Item has been successfully deleted')
		return redirect(url_for('showCategory', category_name = category.name))
	else: 
		return render_template('deleteitem.html', item = itemToDelete)




@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)



if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)















