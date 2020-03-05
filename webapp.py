from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template

import pprint
import os
import json

app = Flask(__name__)

app.debug = True
jsonData="post.json"
postkey = 0

app.secret_key = os.environ['SECRET_KEY']
oauth = OAuth(app)




github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'],
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],
    request_token_params={'scope': 'user:email'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize'
)



@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():

    with open(jsonData) as myjson:
        myFile = json.load(myjson)
    return render_template('home.html', past_posts=posts_to_html())




def posts_to_html():
    table = Markup("<table class='table table-bordered'> <tr> <th> Username </th> <th> Message </th> </tr>")
    try:
        with open(jsonData, 'r+') as j:
            postData=json.load(j)

        for i in postData:
            table += Markup("<tr> <td>" + i["username"] + "</td> <td>" + i["message"] + "</td>")
            if session['user_data']['login'] == i["username"]:
                table += Markup("<td>" + '<button type="button" class="btn btn-secondary">Delete</button>' + "</td>" + "</tr>")

            else:
                table += Markup("</tr>")

    except:
        table += Markup("</table>")
    return table

@app.route('/posted', methods=['POST'])
def post():
    username=session['user_data']['login']
    postText=request.form['message']

    try:
        with open(jsonData, 'r+') as j:
            postData=json.load(j)

            postData.append({ "username":username, "message":postText })

            j.seek(0)
            j.truncate()
            json.dump(postData,j)
            print(postData)
    except Exception as e:
        print("unable to load Json")
        print(e)

    return render_template('home.html', past_posts=posts_to_html())

@app.route('/login')
def login():

    return github.authorize(callback='https://oauth241452351.herokuapp.com/login/authorized')



@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:

        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)
    else:
        try:
            session['github_token'] = (resp['access_token'], '')
            session['user_data']=github.get('user').data
            message='You were successfully logged in as ' + session['user_data']['login']
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('message.html', message=message)


@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run()
