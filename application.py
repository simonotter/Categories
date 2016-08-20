from flask import (Flask, render_template, url_for, request, redirect, flash,
                   session, make_response, jsonify)
from database_setup import Base, Category, Item, User
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc
import random
import string
import json
from oauth2client import client
import requests
import urllib2

app = Flask(__name__)

# Connect to Database and create a database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
db_session = DBSession()


# Create a state token to prevent request forgery.
# Store it in the session for later validation.
@app.route('/signin')
def showSignIn():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    session['state'] = state
    return render_template('signin.html')


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorisation code
    auth_code = request.data
    CLIENT_SECRET_FILE = 'google_client_secret.json'

    # Exchange auth code for access token, refresh token, and ID token
    credentials = client.credentials_from_clientsecrets_and_code(
        CLIENT_SECRET_FILE,
        ['https://www.googleapis.com/auth/drive.appdata', 'profile', 'email'],
        auth_code)

    # Store the access token in the session for later use.
    session['provider'] = 'google'
    session['credentials'] = credentials.access_token
    session['google_id'] = credentials.id_token['sub']
    session['email'] = credentials.id_token['email']

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)

    session['picture'] = data['picture']
    session['username'] = data["name"]

    # check if user already in database, else create the user in the database
    user_id = getUserID(session['google_id'])
    if not user_id:
        user_id = createUser()
    session['user_id'] = user_id

    return session['username']


@app.route('/signOut')
def signOut():
    if 'provider' in session:
        if session['provider'] == 'google':
            del session['credentials']
            del session['google_id']
        del session['provider']
        del session['username']
        del session['user_id']
        del session['email']
        del session['picture']
        flash('You have successfully signed out.')
        return redirect(url_for('showCategories'))
    else:
        flash('You were not logged in to begin with')
        return redirect(url_for('showCategories'))


@app.route('/')
@app.route('/categories')
def showCategories():
    # get all categories and a count of their items
    count_categories = db_session.query(
        Category.name, func.count(Item.id)).outerjoin(Item).group_by(Category.id).all()

    # Get latest top ten items
    items = db_session.query(
        Item).order_by(desc(Item.date_added)).limit(10).all()

    return render_template('categories.html',
                           count_categories=count_categories,
                           items=items)


# API Endpoint (GET Request)
@app.route('/categories/JSON')
def categoriesJSON():
    categories = db_session.query(Category).all()
    return jsonify(categories=[category.serialize for category in categories])


@app.route("/category/new", methods=['GET', 'POST'])
def newCategory():
    if 'user_id' not in session:
        return redirect(url_for('showSignIn'))
    if request.method == 'POST':
        category = Category(name=request.form['name'],
                            user_id=session['user_id'])
        try:
            db_session.add(category)
            db_session.commit()
            flash('New category added.')
            return redirect(url_for('showCategories'))
        except sqlalchemy.exc.IntegrityError, exc:
            print 'caught exception'
            print exc.message
            reason = exc.message
            if reason.find('UNIQUE constraint failed:'):
                db_session.rollback()
                flash("%s already exists" % exc.params[0])
                return render_template('newCategory.html',
                                       mode=None, category=None)
            else:
                return "Problem adding to category to database"
    else:
        return render_template('newCategory.html', mode=None, category=None)


@app.route("/category/<category_name>/")
def showCategory(category_name):
    category = db_session.query(Category).filter_by(name=category_name).one()
    categories = db_session.query(Category).order_by(Category.name).all()
    items = db_session.query(Item).filter_by(category_id=category.id).all()
    return render_template('showCategory.html', category=category,
                           categories=categories, items=items)


@app.route("/category/<category_name>/edit", methods=['GET', 'POST'])
def editCategory(category_name):
    if 'user_id' not in session:
        return redirect(url_for('showSignIn'))
    category = db_session.query(Category).filter_by(name=category_name).one()
    if session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorised \
                to edit this category. Please create your own category \
                in order to edit.');}</script><body onload='myFunction()'>"

    if request.method == 'POST':
        category.name = request.form['name']
        db_session.add(category)
        db_session.commit()
        flash('Category %s has been updated.' % category.name)
        return redirect(url_for('showCategories'))
    else:
        return render_template('newCategory.html',
                               category=category, mode='edit')


@app.route("/category/<category_name>/delete", methods=['GET', 'POST'])
def deleteCategory(category_name):
    if 'user_id' not in session:
        return redirect(url_for('showSignIn'))
    category = db_session.query(Category).filter_by(name=category_name).one()
    if session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorised \
                to delete this category. Please create your own category \
                in order to delete.');}</script><body onload='myFunction()'>"

    if request.method == 'POST':
        # cascade delete items in category or transfer items to new category
        if 'itemOption' in request.form:
            if request.form['itemOption'] == 'moveAllItems':
                # transfer items to new category

                # Check if a valid category has been chosen
                if int(request.form['category']) != 0:
                    db_session.query(Item).filter_by(
                        category_id=category.id).update(
                            {'category_id': int(request.form['category'])})
                else:  # invalid category chosen
                    flash('You must choose a category to move the items to.')
                    item_count = db_session.query(Item).filter_by(
                        category_id=category.id).count()
                    categories = db_session.query(Category).order_by(Category.name).all()
                    categories.remove(category)  # Remove the current category from list
                    return render_template('deleteCategory.html',
                                           category=category, item_count=item_count,
                                           categories=categories)

            if request.form['itemOption'] == 'deleteAllItems':
                # cascade delete items
                db_session.query(Item).filter_by(
                    category_id=category.id).delete()

        db_session.delete(category)
        db_session.commit()
        flash('Category %s has been deleted.' % category_name)
        return redirect(url_for('showCategories'))
    else:
        item_count = db_session.query(Item).filter_by(
            category_id=category.id).count()
        categories = db_session.query(Category).order_by(Category.name).all()
        categories.remove(category)  # Remove the current category from list
        return render_template('deleteCategory.html',
                               category=category, item_count=item_count,
                               categories=categories)


@app.route("/item/<int:item_id>/")
def showItem(item_id):
    item = db_session.query(Item).get(item_id)
    return render_template('showItem.html', item=item)


# API Endpoint (GET Request)
@app.route('/item/<int:item_id>/JSON')
def showItemJSON(item_id):
    item = db_session.query(Item).get(item_id)
    return jsonify(item=item.serialize)


@app.route("/item/new", methods=['GET', 'POST'])
def newItem():
    if 'user_id' not in session:
        return redirect(url_for('showSignIn'))
    if request.method == 'POST':
        item = Item(name=request.form['name'],
                    description=request.form['description'],
                    category_id=int(request.form['category']),
                    user_id=session['user_id'])

        # Check if a valid category has been chosen
        # TODO:UDACITY How should I best handle preventing a user fudging
        # the form submission to give a non-valid category_id? For example,
        # what stops a user putting 99 in request.form['category']
        if int(request.form['category']) != 0:
            db_session.add(item)
            db_session.commit()
            flash('New %s item added.' % item.name)
            return redirect(url_for('showCategories'))
        else:
            categories = db_session.query(
                Category).order_by(Category.name).all()
            category_id = 0
            flash('You must choose a category.')
            # TODO: Need to handle empty item name
            return render_template('newItem.html',
                                   categories=categories, item=item,
                                   category_id=category_id)

    else:  # 'GET' request
        categories = db_session.query(Category).order_by(Category.name).all()

        # Get the category the user came from if available
        index = request.referrer.find('/category/')
        if index != -1:
            # Get the category name after the /category/ and decode it
            category_name = urllib2.unquote(request.referrer[index+10:-1])
            category_id = db_session.query(
                Category).filter_by(name=category_name).one().id
        else:
            category_id = None

        return render_template('newItem.html',
                               categories=categories, item=None,
                               category_id=category_id)


@app.route('/item/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'user_id' not in session:
        return redirect(url_for('showSignIn'))
    item = db_session.query(Item).get(item_id)
    item_name = item.name
    if item.user_id != session['user_id']:
        return "<script>function myFunction() {alert('You are not authorised \
                to delete this item. Please create your own item \
                in order to delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        db_session.delete(item)
        db_session.commit()
        flash('%s item deleted.' % item_name)
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteItem.html', item=item)


@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    if 'user_id' not in session:
        return redirect(url_for('showSignIn'))
    item = db_session.query(Item).get(item_id)
    if item.user_id != session['user_id']:
        return "<script>function myFunction() {alert('You are not authorised \
                to edit this item. Please create your own item \
                in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.category_id = int(request.form['category'])
        db_session.add(item)
        db_session.commit()
        flash('%s item updated.' % item.name)
        return redirect(url_for('showCategories'))
    else:
        categories = db_session.query(Category).order_by(Category.name).all()
        return render_template('newItem.html', categories=categories,
                               item=item, mode='edit')


def createUser():
    newUser = User(name=session['username'],
                   email=session['email'],
                   picture=session['picture'],
                   google_id=session['google_id'])
    db_session.add(newUser)
    db_session.commit()
    return newUser.id


def getUserID(google_id):
    try:
        user = db_session.query(User).filter_by(google_id=google_id).one()
        return user.id
    except:
        return None


if __name__ == "__main__":
    app.debug = True
    app.secret_key = 'Ea02p59M05PiixSw37x3Q5E6w7E8GW79'
    app.run(host='0.0.0.0', port=5000)
