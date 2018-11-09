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
import sqlite3 as lite
from sqlite3 import Error

session_opts = {
    'session.type': 'memory',
    'session.cookie_expires': 300,
    'session.auto': True
}

userHistory = dict()
user_logged_in = False
URL = bottle.request.url

app = SessionMiddleware(bottle.app(), session_opts)
#bottle.run(app=app)

docsSorted = list() #list of urls in display order (highest to lowest pagerank)
searchTerm = str()
page = 1
results_per_page = 5

@get('/')
def hello():
   global user_logged_in
   global URL
   print URL

   if user_logged_in:
       bottle.redirect("http://localhost:8080/login")

   return '''
	<style>
	  .btn {
                padding: 0 20px;
                /* height: 40px; */
                color:blue;
                font-size: 1em;
                font-weight: 900;
                text-transform: uppercase;
                /* border: 3px black solid; */
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
                }
        </style>

        <section id="hero"> 
	<form id="form" method="post">
	    <h1>My Search engine</h1>
	    <input name="keywords" id="keywords" type="text" placeholder="Enter your Phrase"/><br><br>
            <input name="search" id="submit" type="submit" value="Search" class="btn"></input><br>
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
    CLIENT_ID = "568897491390-rbnckuesgmpra3qggo4h4hu9j3qs7m08.apps.googleusercontent.com"
    CLIENT_SECRET = "nRbISCqK45lvYRXzA8l7XpM-"
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
def getResults():
    print request.POST.get('search')

    #search through database for all URLs with first keyword entered by user
    global searchTerm
    global page
    page = 1 #reset to first page of results

    #get user input
    userInput = request.forms.get('keywords')
    userInput = userInput.split()
    searchTerm = userInput[0]

    #search for search term in database, return list of all urls that contain the search term   
    curr=lite.connect("C:\\sqlite\db5\pythonsqlite.db")
    cur=curr.cursor()

    docIdsFromDB = cur.execute("SELECT doc_containing_word FROM WordInfo WHERE word='" + searchTerm + "'") #gets docs containing word
    docIds = ' '.join(c for c in str(docIdsFromDB.fetchone()) if c.isdigit())

    docsAndRanks = list()

    for x in docIds.split():
        docInfoFromDB = cur.execute("SELECT url, pgrank FROM DocInfo WHERE doc_id='" + str(x) + "'").fetchone()
        url = docInfoFromDB[0]
        pageRank = docInfoFromDB[1]

        pair = (url, pageRank)
        docsAndRanks.append(pair)

    #sort urls by pagerank
    global docsSorted
    docsSorted = sorted(docsAndRanks, key=lambda x: x[1], reverse = True)
    print docsSorted

    #display results
    bottle.redirect("http://localhost:8080/results")

@post('/redirect')
def getResultsLoggedIn():
    getResults()

@get('/results')
def displayResults():
    global docsSorted
    global page
    global results_per_page

    output = str()

    if len(docsSorted) > results_per_page:
        output = multiPage(docsSorted, page, results_per_page)
    else:
        output = singlePage(docsSorted) 
    #use post to increment page, display different stuff depending on page
    return output

def multiPage(docList, page=1, results_per_page=5):

    output = '''
            <head>
            <style>
            .btn {
	        padding: 0 20px;
	        height: 40px;
	        color:blue;
	        font-size: 1em;
	        font-weight: 900;
	        text-transform: uppercase;
	        background: transparent;
	        cursor: pointer;
            }
            .pages input {
                color: black
                float: center
                padding: 8px 16px
                text-decoration: none;
            }
            </style>
            <head>
            <body>
            <div class='pages'>
            <form id="switchPage" method="post">'''

    #for i in range(len(docList) / 1):
        #output += "<input name='pg" + str(i) + "' type='submit' value='" + str(i) + "class='btn'></input>"

    for i in range(results_per_page):
        output += "<ul><a href='" + docList[i + results_per_page * (page - 1)][0] + "'>" + docList[i + results_per_page * (page - 1)][0] + "</a></ul>"

    output += "<input name='prev' type='submit' value='<<' class='btn'></input><input name='next' type='submit' value='>>' class='btn'></input></form></div>"

    return output

def singlePage(docList):
    output = str()

    for i in range(len(docList)):
        output += "<ul><a href='" + docList[i][0] + "'>" + docList[i][0] + "</a></ul>"

    return output

@post('/results')
def changePage():
    global page

    if request.POST.get('next'): 
        page += 1
    elif request.POST.get('prev'):
        page -= 1
    else:
        page = '''button clicked''' #user clicked on a page number

    print "hello"
    return displayResults() 
        
    
bottle.run(app=app)
run(host='localhost', port=8080, debug=True) #note: localhost:8080 is hardcoded into login/logout buttons (change this later if possible)
