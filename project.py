__author__ = "QiChen"

from db_setup import Base, Movie, User
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from flask import session as login_session
from flask import make_response

import json
import requests, random, string
import httplib2
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import re

app = Flask(__name__)

APPLICATION_NAME = "Favorite Movies App"

# connect to database and create database session
engine = create_engine('postgres://csajqmbvzicfmy:Ziw2YSvCtPWiYebo6GkSqnEpZN@ec2-54-197-253-142.compute-1.amazonaws.com:5432/d4jhvu06cnvfpe')
# engine = create_engine('sqlite:///movies.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# useful function for reformat youtube url
def reformat(trailer):
  # re-format the movies structure
  youtube_id_match = re.search(r'(?<=v=)[^&#]+', trailer)
  youtube_id_match = youtube_id_match or re.search(r'(?<=be/)[^&#]+', trailer)
  trailer_youtube_id = (youtube_id_match.group(0) if youtube_id_match else None)
  return trailer_youtube_id

### ---------- Basic Actions ---------- ### 
@app.route('/')
@app.route('/movies/')
def showAllMovies():
  movies = session.query(Movie).order_by(asc(Movie.name))
  if 'username' not in login_session:
    return render_template('publicmovies.html', movies=movies)
  else:
    return render_template('movies.html', movies=movies)

@app.route('/movies/new/', methods=['GET', 'POST'])
def newMovie():
  if request.method == 'POST':
    if request.form != []:
      newMovie = Movie(name=request.form['name'], poster=request.form['poster'], trailer=reformat(request.form['trailer']), 
               genre=request.form['genre'], info=request.form['info'])
      session.add(newMovie)
      session.commit()
      flash("New Movie %s was successfully added!" % newMovie.name)
    return redirect(url_for('showAllMovies'))
  else:
    return render_template('newmovie.html')

@app.route('/movies/<int:movie_id>/edit', methods=['GET', 'POST'])
def editMovie(movie_id):
  if 'username' not in login_session:
    return redirect('/login')

  editedMovie = session.query(Movie).filter_by(id=movie_id).one()
  
  if editedMovie.user_id != login_session['user_id']:
    return render_template('failoperate.html')
  
  if request.method == 'POST':
    if request.form['name']:
      editedMovie.name = request.form['name']
    if request.form['trailer']:
      editedMovie.trailer = reformat(request.form['trailer'])
    if request.form['poster']:
      editedMovie.poster = request.form['poster']
    if request.form['genre']:
      editedMovie.genre = request.form['genre']
    if request.form['info']:
      editedMovie.info = request.form['info']
    
    session.add(editedMovie)
    session.commit()
    flash('%s was successfully edited.' % editedMovie.name)
    return redirect(url_for('showAllMovies'))
  else:
    return render_template('editmovie.html', movie=editedMovie)

@app.route('/movies/<int:movie_id>/delete/', methods=['GET', 'POST'])
def deleteMovie(movie_id):
  if 'username' not in login_session:
    return redirect('/login')
  
  deletedMovie = session.query(Movie).filter_by(id=movie_id).one()

  if deletedMovie.user_id != login_session['user_id']:
    return render_template('failoperate.html')
  
  if request.method == 'POST':
    session.delete(deletedMovie)
    flash('%s has been successfully deleted.' % deletedMovie.name)
    session.commit()
    return redirect(url_for('showAllMovies'))
  else:
    return render_template('deletemovie.html', movie=deletedMovie)

@app.route('/movies/yours')
def getYourMovies():
  if 'username' not in login_session:
    return redirect('/login')

  userId = getUserID(login_session['email'])
  movies = session.query(Movie).filter_by(user_id=userId).all()
  return render_template('yourmovies.html', movies=movies)

### ---------- JSON ---------- ### 
@app.route('/movies/JSON')
def moviesJSON():
  movies = session.query(Movie).all()
  return jsonify(movies=[m.serialize for m in movies])

### ---------- Sign in Section ---------- ### 
# Creat anti-forgery state token
@app.route('/login')
def showLogin():
  # one-time code
  state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
  login_session['state'] = state
  return render_template('login.html', STATE=state)

# FB log in
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
  if request.args.get('state') != login_session['state']:
    response = make_response(json.dumps('Invalid state parameter.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  access_token = request.data
  print "access token received %s" % access_token

  app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
  app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']

  url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
  h = httplib2.Http()
  result = h.request(url, 'GET')[1]

  # Use token to get user info from API
  userinfo_url = "https://graph.facebook.com/v2.5/me"
  # strip expire tag from access token
  token = result.split("&")[0]

  # get user email, id... info
  url = 'https://graph.facebook.com/v2.5/me?%s&fields=name,id,email' % token
  h = httplib2.Http()
  result = h.request(url, 'GET')[1]
  data = json.loads(result)
  login_session['provider'] = 'facebook'
  login_session['username'] = data["name"]
  login_session['email'] = data["email"]
  login_session['facebook_id'] = data["id"]
  stored_token = token.split("=")[1]
  login_session['access_token'] =stored_token

  # get user picture
  url = 'https://graph.facebook.com/v2.5/me/picture?%s&redirect=0&height=200&width=200' % token
  h = httplib2.Http()
  result = h.request(url, 'GET')[1]
  data = json.loads(result)
  # login_session['picture'] = data["data"]["url"]

  # see if user exists
  user_id = getUserID(login_session['email'])
  if not user_id:
    user_id = createUser(login_session)
  login_session['user_id'] = user_id

  output = ''
  output += '<h1>Welcome, '
  output += login_session['username']
  output += '!</h1>'
  flash("You are now logged in as %s" % login_session['username'])
  print "done!"
  return output

@app.route('/fblogoff')
def fbdisconnect():
  facebook_id = login_session['facebook_id']
  access_token = login_session['access_token']
  url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
  h = httplib2.Http()
  result = h.request(url, 'DELETE')[1]
  return "You hava been logged out!"

@app.route('/gconnect', methods=['POST'])
def gconnect():
  # validate state token
  if request.args.get('state') != login_session['state']:
    response = make_response(json.dumps('Invalid state parameter.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  # obtain authorization code
  code = request.data

  try:
    # upgrade the authorization code into a credentials object
    oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
    oauth_flow.redirect_uri = 'postmessage'
    credentials = oauth_flow.step2_exchange(code)
  except FlowExchangeError: 
    response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # check that the access token is valid
  access_token = credentials.access_token
  url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
  h = httplib2.Http()
  result = json.loads(h.request(url, 'GET')[1])
  # if there was an error in the access token info, abort
  if result.get('error') is not None:
    response = make_response(json.dumps(result.get('error')), 500)
    response.headers['Content-Type'] = 'application/json'
    return response

  # verify that the access token is used for the intended user
  gplus_id = credentials.id_token['sub']
  if result['user_id'] != gplus_id:
    response = make_response(json.dumps("Token's client ID does not match given user ID."), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  client_id = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

  # verify that the access token is valid for this app
  if result['issued_to'] != client_id:
    response = make_response(json.dumps("Token's client ID does not match app's."),401)
    print "Token's client ID does not match app's."
    response.headers['Content-Type'] = 'application/json'
    return response

  stored_access_token = login_session.get('access_token')
  stored_gplus_id = login_session.get('gplus_id')
  if stored_access_token is not None and gplus_id == stored_gplus_id:
    response = make_response(json.dumps('Current user is already connected'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response

  #  store the access token in the session for later use
  login_session['access_token'] = credentials.access_token
  login_session['gplus_id'] = gplus_id

  # get user info
  userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
  params = {'access_token': credentials.access_token, 'alt': 'json'}
  answer = requests.get(userinfo_url, params=params)

  data = answer.json()

  login_session['username'] = data['name']
  # login_session['picture'] = data['picture']
  login_session['email'] = data['email']
  login_session['provider'] = 'google'

  # check if user exists, if not, make a new one
  user_id = getUserID(login_session['email'])
  if not user_id:
    user_id = createUser(login_session)
  login_session['user_id'] = user_id

  output = ''
  output += '<h1>Welcome, '
  output += login_session['username']
  output += '!</h1>'
  flash("You are now logged in as %s" % login_session['username'])
  print "done!"
  return output

# disconnect with goolge plus
@app.route('/gdisconnect')
def gdisconnect():
  access_token = login_session['access_token']
  print 'In google+ log off access token is %s', access_token
  print 'User name is: %s' % login_session['username']
  if access_token is None:
    print 'Access Token is None'
    response = make_response(json.dumps('Current user is not connected.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
  h = httplib2.Http()
  result = h.request(url, 'GET')[0]
  print "Result is %s" % result
  if result['status'] == '200': #log off successfully
    del login_session['access_token']
    del login_session['gplus_id']

    response = make_response(json.dumps("Successfully logged off."), 200)
    response.headers['Content-Type'] = 'application/json'
    return response
  else:
    response = make_response(json.dumps("Failed to revoke token for given user."), 400)
    response.headers['Content-Type'] = 'application/json'
    return response


# disconnect based on provider
@app.route('/disconnect')
def disconnect():
  if 'provider' in login_session:
    if login_session['provider'] == 'google':
      gdisconnect()

    if login_session['provider'] == 'facebook':
      fbdisconnect()
      del login_session['facebook_id']
    
    del login_session['username']
    del login_session['email']
    del login_session['user_id']
    del login_session['provider']
    # flash("You have successfully been logged out.")
    return redirect(url_for('showAllMovies'))
  else:
    # flash("You were not logged in.")
    return redirect(url_for('showAllMovies'))

### ---------- Basic User Information ---------- ### 
# User functions
def createUser(login_session):
  newUser = User(name=login_session['username'], email=login_session['email'])
  session.add(newUser)
  session.commit()
  user = session.query(User).filter_by(email=login_session['email']).one()
  return user.id

def getUserInfo(user_id):
  user = session.query(User).filter_by(id=user_id).one()
  return user

def getUserID(email):
  try:
    user = session.query(User).filter_by(email=email).one()
    return user.id
  except:
    return None

# if __name__ == '__main__':
app.secret_key = 'super_secret_key'
app.debug = True
# app.run('', port = 5000)
