# coding: utf-8

import bottle
from bottle import route, run, get, post, request, response, template, app
import httplib2
from httplib2 import Http
import requests
import credentials
from beaker.middleware import SessionMiddleware
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

session_opts = {
    'session.type': 'memory',
    'session.cookie_expires': 300,
    'session.auto': True
}

userHistory = dict()
user_logged_in = False

app = SessionMiddleware(bottle.app(), session_opts)
#bottle.run(app=app)

@get('/')
def hello():
   global user_logged_in

   if user_logged_in:
       bottle.redirect("http://localhost:8080/login")

   return '''
	<style><!--css stuff here-->
	  .btn {
	  padding: 0 20px;
	  height: 40px;
	  color:blue;
	  font-size: 1em;
	  font-weight: 900;
	  text-transform: uppercase;
	  border: 3px black solid;
	  border-radius: 2px;
	  background: transparent;
	  cursor: pointer;
	 
		
	}
	#hero {
	  display: flex;
	  flex-direction: column;
	  align-items: center;
	  
	  justify-content: center;
	  text-align: center;
	  height: 200px;
	  margin-top: 50px;
	  h2 {
		margin-bottom: 20px;
		word-wrap: break-word;
	  }
	  input[type="email"] {
		max-width: 275px;
		width: 100%;
		padding: 5px;
	  }
	  input[type="submit"] {
		max-width: 150px;
		width: 100%;
	user_logged_in = True	height: 30px;
		margin: 15px 0;
		border: 0;
		background-color: #f1c40f;
		
		&:hover {
		  background-color: orange;
		  transition: background-color 1s;
		}
	  }
	 </style><!--css stuff ends here-->

	<form id="form" method="post">
	<section id="hero"> 
	    <h1>My Search engine</h1>
	    <input name="keywords" id="keywords" type="text" placeholder="Enter your Phrase"/><br><br><input name="search" id="submit" type="submit" value="Search" class="btn"></input><br>
	</form>
        <a href="http://localhost:8080/login"><button id="login" type="button" class="btn">Log In</button></a>
	</section>
	</html>
'''

@get('/login')
def login():
    global user_logged_in
    user_logged_in = True

    flow = flow_from_clientsecrets("client_secret.json", scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email', redirect_uri="http://localhost:8080/redirect")
    uri = flow.step1_get_authorize_url()
    print user_logged_in
    print str(uri)
    bottle.redirect(str(uri))

@get('/redirect')
def redirect_page():
    global user_logged_in

    if not user_logged_in:
       bottle.redirect("http://localhost:8080")

    code = request.query.get('code', '')
    CLIENT_ID = #insert client ID here
    CLIENT_SECRET = #insert client secret here
    SCOPE = 'https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email'

    flow = OAuth2WebServerFlow(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scope=SCOPE, redirect_uri="http://localhost:8080/redirect")
    credentials = flow.step2_exchange(code)
    token = credentials.id_token['sub']

    response.set_cookie("token", str(token)) #store token

    http = httplib2.Http()
    http = credentials.authorize(http)
    
    # Get user email
    users_service = build('oauth2', 'v2', http=http)
    user_document = users_service.userinfo().get().execute()
    user_email = user_document['email']

    response.set_cookie("email", str(user_email)) #store user's email

    output = '''
	<style><!--css stuff here-->
	  .btn {
	  padding: 0 20px;
	  height: 40px;
	  color:blue;
	  font-size: 1em;
	  font-weight: 900;
	  text-transform: uppercase;
	  border: 3px black solid;
	  border-radius: 2px;
	  background: transparent;
	  cursor: pointer;
	 
		
	}
	#hero {
	  display: flex;
	  flex-direction: column;
	  align-items: center;
	  
	  justify-content: center;
	  text-align: center;
	  height: 200px;
	  margin-top: 50px;
	  h2 {
		margin-bottom: 20px;
		word-wrap: break-word;
	  }
	  input[type="email"] {
		max-width: 275px;
		width: 100%;
		padding: 5px;
	  }
	  input[type="submit"] {
		max-width: 150px;
		width: 100%;
		height: 30px;
		margin: 15px 0;
		border: 0;
		background-color: #f1c40f;
		
		&:hover {
		  background-color: orange;
		  transition: background-color 1s;
		}
	  }
	 </style><!--css stuff ends here-->'''
    output += '''<h3>''' + user_email + '''</h3><br>'''
    output += '''
        <form id="form" method="post">
	<section id="hero"> 
	    <h1>My Search engine</h1>
	    <input name="keywords" id="keywords" type="text" placeholder="Enter your Phrase"/><br><br><input name="search2" id="submit" type="submit" value="Search" class="btn"></input><br>
	</form>
        <a href="http://localhost:8080/logout"><button id="logout" type="button" class="btn">Log Out</button></a>
	</section>
	</html>
'''

    return output

@get('/logout')
def logout():
    global user_logged_in
    user_logged_in = False;

    token = request.get("token")
    requests.post('https://accounts.google.com/o/oauth2/revoke', params={'token': token}, headers = {'content-type': 'application/x-www-form-urlencoded'})
    bottle.redirect("http://localhost:8080")

#@route('/output')
#def session_output():
#    s = bottle.request.environ.get('beaker.session')
#    return s['test']

@post('/')
def displayResults():
        output = '''<a href="http://localhost:8080/login"><button id="login" type="button" class="btn">Log In</button></a>'''
        #results table
	userInput = request.forms.get('keywords')
	words = userInput.split()
	dictionary = dict()

        #count number of times each word was entered
	for x in words:
	    if dictionary.has_key(x):
		dictionary[x] += 1
	    else:
		dictionary[x] = 1
	
        #create results table
	output += "<h2>Search Results</h2><table name=\"results\"><tr><th>Word</th><th>Count</th><tr>"
	
        #add a row to the results table for each word the user has entered
	for key, value in dictionary.iteritems():
	    output += "<tr><td>" + key + "</td><td> &nbsp;&nbsp;&nbsp;&nbsp;" + str(value) + "</td></tr>"
        
        output += "</table>"

	return output

@post('/redirect')
def displayResults():
        user_email = request.get_cookie("email")
        output = '''<h3>''' + user_email + '''</h3><br><a href="http://localhost:8080/logout"><button id="logout" type="button" class="btn">Log Out</button></a>'''
        global userHistory

        #results table
	userInput = request.forms.get('keywords')
	words = userInput.split()
	dictionary = dict()

        #count number of times each word was entered
	for x in words:
	    if dictionary.has_key(x):
		dictionary[x] += 1
	    else:
		dictionary[x] = 1
	
        #create results table
	output += "<h2>Search Results</h2><table name=\"results\"><tr><th>Word</th><th>Count</th><tr>"
	
        #add a row to the results table for each word the user has entered
	for key, value in dictionary.iteritems():
	    output += "<tr><td>" + key + "</td><td> &nbsp;&nbsp;&nbsp;&nbsp;" + str(value) + "</td></tr>"
        
        output += "</table>"

        #top 20 keywords table
        s = bottle.request.environ.get('beaker.session')

        if user_email not in userHistory: #create data for user if their email hasn't been used yet
            userHistory[user_email] = userInput + " "
        else:
            userHistory[user_email] += userInput + " "

        keywords = userHistory[user_email]
        
        keywords_split = keywords.split()
        keywordsFreqs = dict()

        for x in keywords_split:
            if keywordsFreqs.has_key(x):
                keywordsFreqs[x] += 1
            else:
                keywordsFreqs[x] = 1

        #create history table
        output += "<br><br><h2>Most Popular Keywords</h2><table name=\"history\"><tr><th>Word</th><th>Count</th><tr>"

        #add a row to the history table for each word stored
	counter = 0

        for i in range(20):
            if i > (len(keywordsFreqs) - 1):
                break

            maxIndex = str()
            maxVal = 0

            for key, value in keywordsFreqs.iteritems():
                if value > maxVal:
                    maxIndex = key
                    maxVal = value

            keywordsFreqs[maxIndex] = 0
            output += "<tr><td>" + maxIndex + "</td><td> &nbsp;&nbsp;&nbsp;&nbsp;" + str(maxVal) + "</td></tr>"

        output += "</table>"

	return output

bottle.run(app=app)
run(host='localhost', port=8080, debug=True) #note: localhost:8080 is hardcoded into login/logout buttons (change this later if possible)
