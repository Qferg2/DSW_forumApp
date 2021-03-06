from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template
from bson.objectid import ObjectId

import pymongo
import os
import sys
import pprint

# This code originally from https://github.com/lepture/flask-oauthlib/blob/master/example/github.py
# Edited by P. Conrad for SPIS 2016 to add getting Client Id and Secret from
# environment variables, so that this will work on Heroku.
# Edited by S. Adams for Designing Software for the Web to add comments and remove flash messaging

app = Flask(__name__)

app.debug = True #Change this to False for production

app.secret_key = os.environ['SECRET_KEY']
oauth = OAuth(app)

connection_string = os.environ["MONGO_CONNECTION_STRING"]
db_name = os.environ["MONGO_DBNAME"]
client = pymongo.MongoClient(connection_string)
db = client[db_name]
collection = db['Data']


#Set up Github as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'],
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)


@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https'))

@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You were logged out')

@app.route('/login/authorized')#the route should match the callback URL registered with the OAuth provider
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)
    else:
        try:
            #save user data and set log in message
            session["github_token"] = (resp['access_token'], '')
            session['user_data'] = github.get('user').data
            if session['user_data']['public_repos'] > 9:
                message = 'You were successfully logged in as ' + session['user_data']['login']
            else:
                session.clear()
                message = 'Unable to login. You are not qualified to view this content.'
        except Exception as inst:
            #clear the session and give error message
            session.clear()
            print(inst)
            message = 'Unable to login. Please try again.'
    return render_template('message.html', message=message)


@app.route('/page1', methods=['GET','POST'])
def renderPage1():
    options=''
    if 'user_data' in session:
        if 'data' in request.form:
            input = request.form['data']
            document = {'User':session['user_data']['login'], 'Message':input}
            posts = db.Data
            post_id = posts.insert_one(document).inserted_id
            print(post_id)
        posts = db.Data
        if 'delete' in request.form: 
            id = ObjectId(request.form['delete'])
            posts.delete_one({'_id':id})
        for document in posts.find():
            options += document['User'] + '\t' + document['Message'] + '\n' + Markup('<form action="/page1" method="post"> <button type="submit" name="delete" value="'+str(document["_id"])+'">Delete</button> </form>')
        print("")
        
    return render_template('page1.html', testdata = options)


@github.tokengetter
def get_github_oauth_token():
    return session['github_token']



if __name__ == '__main__':
    app.run()
