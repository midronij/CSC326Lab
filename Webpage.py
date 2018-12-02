# coding: utf-8

import bottle
from bottle import route, run, get, post, request, response, template, app, error
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
import pygtrie as trie
t = trie.StringTrie()
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
email = str()
interp = str() #calculate:, define:, etc.
answer = 0.0
flagset=True
suggest=list() #list of related search suggestions
userInput = str()
inputFromSuggestion = False

@get('/')
#starting html page
def hello():
   global user_logged_in
   global URL
   global flagset
   if flagset:
       flagset=False
       setTrie()
   if user_logged_in:
       bottle.redirect("http://localhost:8080/login")

   return '''
<html>
<head>
	<style>	
	body {
		background-image: linear-gradient(to top, #f4fdff, white);
		background-repeat: no-repeat;
		height: 100%;
		overflow: hidden;
		}
	
	.main {
		position: absolute;
		top: 45%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
		}
	.search-box {
		height: 30px;
		border-radius: 40px;
		padding: 10px;
		border-style: solid;
		border-color: #72e7ff;
		background: white;
		transition: 0.4s;
		box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
		}
				
	.search-box:hover, .search-box:focus-within {
		height: 40px;
		background: #72e7ff;
		box-shadow: none;
		}
	
	.search-txt {
		border: none;
		background: none;
		outline: none;
		float: center;
		text-align: center;
		padding: 0;
		color: #036c82;
		font-size: 20px;
		line-height: 40px;
		width: 800px;
		}
			
	#submit {
		border: none;
		background: white;
		transition: 0.4s;
		border-radius: 40px;
		width: 200px;
		line-height: 30px;
		box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.2), 0 3px 10px 0 rgba(0, 0, 0, 0.19);
		font-size: 16px;
		}
		
	#submit:hover {
		background: #72e7ff;
		border-color: #72e7ff;
		border-style: solid;
		border-width: 5px;
		box-shadow: none;
		}
	
	.nav {
		background: #72e7ff;
		width: 100%;
		height: 8%;
		padding: 0;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2), 0 2px 5px 0 rgba(0, 0, 0, 0.19);
		padding-top: 0.5%;
		padding-right: 5%;
		}
		
	#login {
		border: none;
		background: white;
		transition: 0.4s;
		border-radius: 40px;
		height: 50px;
		width: 150px;
		line-height: 30px;
		font-size: 16px;
		float: right;
		margin-bottom: 1%;
		margin-top: 0.5%;
		}
		
	#login:hover {
		border-color: white;
		border-style: solid;
		border-width: 3px;
		background: #72e7ff;
		color: #036c82;
		font-weight: bold;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2), 0 2px 5px 0 rgba(0, 0, 0, 0.19);
		}
		
	#toptext {
		float: left;
		font-family: sans-serif;
		padding-left: 1%;
		color: 036c82;
		font-style: italic;
		}
		
	#title {
		color: #036c82;
		font-family: sans-serif;
		font-size: 48px;
		}

        #help {
		background: white;
		transition: 0.4s;
		border-radius: 40px;
		width: 50px;
		line-height: 30px;
		box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.2), 0 3px 10px 0 rgba(0, 0, 0, 0.19);
		font-size: 16px;
		border: none;
	}
	
	#help:hover {
		background: #72e7ff;
		box-shadow: none;
		}
	
	#help:hover ~ #tips{
		visibility: visible;
		}
		
	#tips {
		visibility: hidden;
		transition: 0.2s;
		text-align: center;
		color: #036c82;
		font-family: sans-serif;
		border-color: #72e7ff;
		border-style: solid;
		border-width: 3px;
		background-color: white;
		box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
		padding-left: 3%;
		padding-right: 3%;
		}
		
	h3 {
		font-size: 24px;
		}
		
	p {
		font-size: 20px;
		}
	
    </style>
</head>
<body>
	<section id="hero">
	<div class="nav">
		<h2 id="toptext">You are not logged in.</h2>
		<a href="http://localhost:8080/login"><button id="login" type="button" class="btn">Log In</button></a>
	</div>
	<div class="main">
		<form id="form" method="post" autocomplete="off">
			<h1 id="title">Search the web:</h1>
			<div class="search-box">
				<input name="keywords" id="keywords" type="text" placeholder="Enter your phrase..." class="search-txt" oninput="getSuggestions()"/>
			</div>
			<br><br><input name="search" id="submit" type="submit" value="Search" class="btn"></input>
                        <button id="help" type="button" class="btn">?</button><br><br>
			<div id="tips">
				<h3>Search tips:</h3>
				<p>To perform mathematical calculations, type "Calculate:" followed by the expression you want to calculate."</p>
				<p>To get the definition of a word, type "Define:" followed by the word you want to know.</p>
			</div>
		</form>
	</div>
    </section>

<script type="module">
	import {saveAs} from 'file-saver';

	function getSuggestions()
	{
		var keywords = document.getElementById("keywords").value;
		saveFile(keywords, "File.txt");
	}
     
	function download(data, filename, type) 
	{
	    var file = new Blob([data], {type: type});
	    if (window.navigator.msSaveOrOpenBlob) // IE10+
		window.navigator.msSaveOrOpenBlob(file, filename);
	    else { // Others
		var a = document.createElement("a"),
		        url = URL.createObjectURL(file);
		a.href = url;
		a.download = filename;
		document.body.appendChild(a);
		a.click();
		setTimeout(function() {
		    document.body.removeChild(a);
		    window.URL.revokeObjectURL(url);  
		}, 0); 
	    }
	}

	function createFile(data, filename, type)
	{
	    var a = document.getElementById("keywords");
	    var file = new Blob([data], {type: type});
	    a.href = URL.createObjectURL(file);
	    a.download = name;
	}

        function saveFile(data, filename)
	{
	    var blob = new Blob([data], {type: "text/plain;charset=utf-8"});
	    saveAs(blob, filename);
	}
</script>
</body>
</html>
'''


'''Insert into Trie data structure'''


def setTrie():
   curr = lite.connect("C:\\sqlite\db5\pythonsqlite.db")
   cur = curr.cursor()
   words = cur.execute("SELECT word FROM WordInfo").fetchall()
   global t
   for x in words:
      word=x[0]
      key = str()
      for y in word:
        key += y
        t[key+ "/" + word] = word


'''function to login to your account'''


@get('/login')
def login():
    global user_logged_in
    user_logged_in = True

    flow = flow_from_clientsecrets("client_secret.json", scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email', redirect_uri="http://localhost:8080/redirect")
    uri = flow.step1_get_authorize_url()
    bottle.redirect(str(uri))


'''redirect page '''


@get('/redirect')
def redirect_page():
    global user_logged_in

    if not user_logged_in:
       bottle.redirect("/")

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
<html>
<head>
	<style>	
	body {
		background-image: linear-gradient(to top, #f4fdff, white);
		background-repeat: no-repeat;
		height: 100%;
		overflow: hidden;
		}
	
	.main {
		position: absolute;
		top: 45%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
		}
	.search-box {
		height: 30px;
		border-radius: 40px;
		padding: 10px;
		border-style: solid;
		border-color: #72e7ff;
		background: white;
		transition: 0.4s;
		box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
		}
				
	.search-box:hover, .search-box:focus-within {
		height: 40px;
		background: #72e7ff;
		box-shadow: none;
		}
	
	.search-txt {
		border: none;
		background: none;
		outline: none;
		float: center;
		text-align: center;
		padding: 0;
		color: #036c82;
		font-size: 20px;
		line-height: 40px;
		width: 800px;
		}
			
	#submit {
		border: none;
		background: white;
		transition: 0.4s;
		border-radius: 40px;
		width: 200px;
		line-height: 30px;
		box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.2), 0 3px 10px 0 rgba(0, 0, 0, 0.19);
		font-size: 16px;
		}
		
	#submit:hover {
		background: #72e7ff;
		border-color: #72e7ff;
		border-style: solid;
		border-width: 5px;
		box-shadow: none;
		}
	
	.nav {
		background: #72e7ff;
		width: 100%;
		height: 8%;
		padding: 0;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2), 0 2px 5px 0 rgba(0, 0, 0, 0.19);
		padding-top: 0.5%;
		padding-right: 5%;
		}
		
	#login {
		border: none;
		background: white;
		transition: 0.4s;
		border-radius: 40px;
		height: 50px;
		width: 150px;
		line-height: 30px;
		font-size: 16px;
		float: right;
		margin-top: 0.5%;
		}
		
	#login:hover {
		border-color: white;
		border-style: solid;
		border-width: 3px;
		background: #72e7ff;
		color: white;
		font-weight: bold;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2), 0 2px 5px 0 rgba(0, 0, 0, 0.19);
		}
		
	#toptext {
		float: left;
		font-family: sans-serif;
		padding-left: 1%;
		color: #036c82;
		font-style: italic;
		}
		
	#title {
		color: #036c82;
		font-family: sans-serif;
		font-size: 48px;
		}

	#help {
		background: white;
		transition: 0.4s;
		border-radius: 40px;
		width: 50px;
		line-height: 30px;
		box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.2), 0 3px 10px 0 rgba(0, 0, 0, 0.19);
		font-size: 16px;
		border: none;
	}
	
	#help:hover {
		background: #72e7ff;
		box-shadow: none;
		}
	
	#help:hover ~ #tips{
		visibility: visible;
		}
		
	#tips {
		visibility: hidden;
		transition: 0.2s;
		text-align: center;
		color: #036c82;
		font-family: sans-serif;
		border-color: #72e7ff;
		border-style: solid;
		border-width: 3px;
		background-color: white;
		box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
		padding-left: 3%;
		padding-right: 3%;
		}
		
	h3 {
		font-size: 24px;
		}
		
	p {
		font-size: 20px;
		}
	
    </style>
</head>
<body>
	<section id="hero">
	<div class="nav">'''
    output += '''<h2 id="toptext">Welcome, ''' + user_email + '''.</h2>'''
    output += '''
<a href="http://localhost:8080/logout"><button id="login" type="button" class="btn">Log Out</button></a>
	</div>
	<div class="main">
		<form id="form" method="post">
			<h1 id="title">Search the web:</h1>
			<div class="search-box">
				<input name="keywords" id="keywords" type="text" placeholder="Enter your phrase..." class="search-txt"/>
			</div>
			<br><br><input name="search" id="submit" type="submit" value="Search" class="btn"></input>
			<button id="help" type="button" class="btn">?</button><br><br>
			<div id="tips">
				<h3>Search tips:</h3>
				<p>To perform mathematical calculations, type "Calculate:" followed by the expression you want to calculate."</p>
				<p>To get the definition of a word, type "Define:" followed by the word you want to know.</p>
			</div>
		</form>
	</div>
    </section>
<body>
</html>
'''
    return output

'''logout functionality'''


@get('/logout')
def logout():
    global user_logged_in
    user_logged_in = False;

    token = request.get("token")
    requests.post('https://accounts.google.com/o/oauth2/revoke', params={'token': token}, headers = {'content-type': 'application/x-www-form-urlencoded'})
    bottle.redirect("/")

#@route('/output')
#def session_output():
#    s = bottle.request.environ.get('beaker.session')
#    return s['test']


''' Computations for Results page'''


@post('/')
def getResults():
    print request.POST.get('search')
    global interp
    global answer #used for answer to mathematical expression or definition of given word
    global suggest
    global inputFromSuggestion
    global userInput

    global searchTerm
    global page
    page = 1 #reset to first page of results

    print str(inputFromSuggestion)
    #get user input
    if not inputFromSuggestion:
        userInput = request.forms.get('keywords')
    
    inputFromSuggestion = False;

    #check for special keyswords ('calculate', 'define', etc)
    if (userInput.lower()).startswith("calculate:"):
        interp = "calc"
        expression = (userInput.lower()).replace('calculate:', '')
        searchTerm = expression + ' ='   
        answer = eval(expression)

    elif (userInput.lower()).startswith("define:"):
        interp = "def"
        searchTerm = ((userInput.lower()).replace('define:','')).lstrip() #remove "define" keyword and any leading whitespace
        answer = list()

        #search the dictionary for the given word
        curr = lite.connect("Dictionary.db")
        cur = curr.cursor()

        #get word type (i.e.: adjective, noun, verb, etc.)        
        wordTypesFromDB = cur.execute("SELECT wordtype FROM entries WHERE word='" + searchTerm.capitalize() + "'")
        wordTypes = wordTypesFromDB.fetchall()

        #get definition
        definitionsFromDB = cur.execute("SELECT definition FROM entries WHERE word='" + searchTerm.capitalize() + "'")
        definitions = definitionsFromDB.fetchall()

        for i in range(len(definitions)):
            answer.append(str(wordTypes[i][0]) + ": " + str(definitions[i][0]).replace('\n', ''))

        if not answer: #i.e.: word is not in dictionary
            answer.append("No definition found.")

    else:
        interp = ""

        #get search suggestions
        checkInput = userInput
        suggest = list()
        if t.has_subtrie(''+(checkInput)):
            suggest = list(t[''+(checkInput)+'':])

        print suggest

        #search through database for all URLs with first keyword entered by user
        userInput = userInput.split()
        searchTerm = userInput[0]

        #search for search term in database, return list of all urls that contain the search term   
        curr = lite.connect("C:\\sqlite\db5\pythonsqlite.db")
        cur = curr.cursor()

        docIdsFromDB = cur.execute("SELECT doc_containing_word FROM WordInfo WHERE word='" + searchTerm + "'") #gets docs containing word    

        dbOutput = str(docIdsFromDB.fetchone())
        docIds = str()
        for i in range(len(dbOutput)):
            if dbOutput[i].isdigit() or dbOutput[i] == ' ':
                docIds += dbOutput[i]
    
        #docIds = ' '.join(c for c in str(docIdsFromDB.fetchone()) if c.isdigit() and not c.next().isdigit())
        print docIds

        docsAndRanks = set()

        for x in docIds.split():
            docInfoFromDB = cur.execute("SELECT url, pgrank, images FROM DocInfo WHERE doc_id='" + str(x) + "'").fetchone()
            url = docInfoFromDB[0]
            pageRank = docInfoFromDB[1]
            images = docInfoFromDB[2].split()
            pair = tuple()

            if not images:
                pair = (url, pageRank, "No images")
            else:
                pair = (url, pageRank, images[0])
            docsAndRanks.add(pair)

        #sort urls by pagerank
        global docsSorted
        docsSorted = sorted(list(docsAndRanks), key=lambda x: x[1], reverse = True)

    #display results
    bottle.redirect("/results")


''' Function to get Results to display '''


@post('/redirect')
def getResultsLoggedIn():
    getResults()


'''The below function displays Results'''


@get('/results')
def displayResults():
    global docsSorted
    global page
    global results_per_page
    global searchTerm
    global user_logged_in
    global answer
    global suggest

    output = '''
<html>
<head>
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
	<style>	
	body {
		background-image: linear-gradient(to top, #f4fdff, white);
		background-repeat: no-repeat;
		height: 100%;
		overflow: hidden;
		}
	
	.main {
		position: absolute;
		top: 45%;
		left: 50%;
		transform: translate(-50%, -50%);
		}
		
	.search-box {
		height: 30px;
		border-radius: 40px;
		padding: 10px;
		border-style: solid;
		border-color: #72e7ff;
		background: white;
		transition: 0.4s;
		float: left;
		width: 20%;
		padding-left: 1%;
		}
				
	.search-box:hover, .search-box:focus-within {
		background: #72e7ff;
		box-shadow: none;
		border-color: white;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2), 0 2px 5px 0 rgba(0, 0, 0, 0.19);
		}
	
	.search-txt {
		border: none;
		background: none;
		outline: none;
		float: left;
		text-align: left;
		padding: 0;
		color: #036c82;
		font-size: 20px;
		line-height: 40px;
		width: 800px;
		}
			
	#submit {
		height: 50px;
		width: 60px;
		border: none;
		background: white;
		transition: 0.4s;
		border-radius: 40px;
		line-height: 30px;
		font-size: 16px;
		margin-left: 10px;
		margin-top: 0.2%;
		}
		
	#submit:hover {
		background: #72e7ff;
		border-color: #72e7ff;
		border-style: solid;
		border-width: 5px;
		box-shadow: none;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2), 0 2px 5px 0 rgba(0, 0, 0, 0.19);
		border-color: white;
		border-width: 3px;
		}
	
	.nav {
		background: #72e7ff;
		width: 100%;
		height: 8%;
		padding: 0;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2), 0 2px 5px 0 rgba(0, 0, 0, 0.19);
		padding-top: 0.5%;
		padding-right: 0.5%;
		padding-left: 0.2%;
		}
		
	#login {
		border: none;
		background: white;
		transition: 0.4s;
		border-radius: 40px;
		height: 50px;
		width: 150px;
		line-height: 30px;
		font-size: 16px;
		float: right;
		margin-top: 0.5%;
		}
		
	#login:hover {
		border-color: white;
		border-style: solid;
		border-width: 3px;
		background: #72e7ff;
		color: white;
		font-weight: bold;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2), 0 2px 5px 0 rgba(0, 0, 0, 0.19);
		}
		
	#toptext {
		float: right;
		font-family: sans-serif;
		margin-right: 1%;
		color: #036c82;
		font-style: italic;
		
		}
	#title {
		color: #036c82;
		font-family: sans-serif;
		font-size: 48px;
		}
		
	.results, .results2, .images {
		border-color: #036c82;
		border-style: solid;
		border-width: 3px;
		font-size: 20px;
		font-family: sans-serif;
		background-color: white;
		box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
		}

	.results, .images {
		text-align: left;
		}

	.results2 {
		text-align: center;
		}

	.images {
		position: absolute;
		left: 65%;
		width: 30%;
		bottom: 25%;
		height: 40%;
		float: right;
		text-align: center;
		}
		
	ul {
		padding-bottom: 20px;
		color: #036c82;
		}
		
	.pages {
		position: absolute;
		top: 85%;
		left: 50%;
		transform: translate(-50%, -50%);
		}
		
	#prev, #next {
		height: 50px;
		width: 60px;
		border: none;
		background: white;
		transition: 0.4s;
		border-radius: 40px;
		line-height: 30px;
		font-size: 16px;
		margin-left: 10px;
		margin-top: 0.2%;
		box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.2), 0 3px 10px 0 rgba(0, 0, 0, 0.19);
		font-weight: bold;
		}
		
	#prev:hover, #next:hover {
		background: #72e7ff;
		border-color: #72e7ff;
		border-style: solid;
		border-width: 5px;
		box-shadow: none;
		border-color: white;
		border-width: 3px;
		}
     
        #answer {
		color: #036c82;
                font-size: 40px;
                }

        #def {
		color: #036c82;
		font-size: 20px;
		margin-left: 5%;
		}

	.sugg {
		height: 50px;
		border: none;
		background: white;
		transition: 0.4s;
		border-radius: 40px;
		line-height: 30px;
		font-size: 16px;
		margin-left: 10px;
		margin-top: 0.2%;
		box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.2), 0 3px 10px 0 rgba(0, 0, 0, 0.19);
		font-weight: bold;
		padding-left: 2%;
		padding-right: 2%;
		font-family: sans-serif;
		}
	
	.sugg:hover {
		background: #72e7ff;
		border-color: #72e7ff;
		border-style: solid;
		border-width: 5px;
		box-shadow: none;
		border-color: white;
		border-width: 3px;
		}
		
	#sTitle {
		color: #036c82;
		font-family: sans-serif;
		font-size: 36px;
		padding-left: 0.75%
		padding-top: 1%;
		}

	.icon {
		margin-right: 2%;
		width: 30px;
		height: 30px;
		}
		
	#img_link0, #img_link1, #img_link2, #img_link3, #img_link4 {
		visibility: hidden;
		}
	
    </style>
</head>
<body>
	<section id="hero">
	<div class="nav">
		<form id="form" method="post">
			<div class="search-box">
				<input name="keywords" id="keywords" type="text" placeholder="Search..." class="search-txt"/>
			</div>
			<input name="search" id="submit" type="submit" class="btn" value="Go"></input>'''

    if user_logged_in:
        output+= '''<a href="http://localhost:8080/logout"><button id="login" type="button" class="btn">Log Out</button></a><h2 id="toptext">''' + str(request.get_cookie("email")) + '''</h2>'''
    else:
        output+= '''<a href="http://localhost:8080/login"><button id="login" type="button" class="btn">Log In</button></a>'''

    if interp == "calc":
        output += '''</form></div><div class="main"><h2 id="title">''' + searchTerm + '''</h2>
                     <div class="results2"><h2 id="answer">''' + str(answer) + '''</h2></div></div></section><body></html>'''
    elif interp == "def":
        if len(answer) <= 1:
            output += '''</form></div><div class="main"><h2 id="title">Definition for "''' + searchTerm + '''":</h2>
                         <div class="results"><h2 id="def">''' + answer[0] + '''</h2></div></div></section><body></html>'''
        else:
            output += '''</form></div><div class="main"><h2 id="title">Definition for "''' + searchTerm +'''":</h2>''';
            output += multiPage(answer, page, 1) #display one definition per page
    else:
	output += '''</form></div>'''
        
        #we don't want to suggest searches if there are no other searches to suggest
        if len(suggest) <= 1:
            if suggest and suggest[0] == searchTerm:
                pass
            else:
                pass
        else:
            output +='''<form id="suggest" method="post"><div class="suggestions"><h2 id="sTitle">Related searches:</h2>'''

        for i in range(len(suggest)):
            if i > 3:
                break
            if suggest[i] != searchTerm:
                output += '''<input name="''' + suggest[i] + '''" id="''' + suggest[i] + '''" type="submit" value="''' + suggest[i] +'''" class="sugg"></input><br><br>'''

        output += '''</div></form></div><div class="main"><h2 id="title">Results for "''' + searchTerm +'''":</h2>''';

        if len(docsSorted) == 0:
            output += '''<div class="results"><ul>No results found.</ul></div>'''
        elif len(docsSorted) > results_per_page:
            output += multiPage(docsSorted, page, results_per_page)
        else:
            output += singlePage(docsSorted) 

    return output

#use post to increment page, display different stuff depending on page


def multiPage(docList, page=1, results_per_page=5):
    global interp

    output = '''<div class="results">''';

    #for i in range(len(docList) / 1):
        #output += "<input name='pg" + str(i) + "' type='submit' value='" + str(i) + "class='btn'></input>"
    resultsOnCurrentPage = 0

    for i in range(results_per_page):
        if (results_per_page * page + i <= len(docList)):
           if interp == "def":
               output += '''<h2 id="def">''' + docList[i + results_per_page * (page - 1)] + '''</h2>'''
           else:
               resultsOnCurrentPage += 1
               #output += '''<ul><img src="camera.png" id="show_img"''' + str(i) + '''class="icon" onmouseover="document.getElementById('img_link''' + str(i) + '''').style.visibility = 'visible';" onmouseout="document.getElementById('img_link''' + str(i) + '''').style.visibility = 'hidden';"></img>'''
               output += '''<ul><a href="''' + docList[i + results_per_page * (page - 1)][0] + '''">''' + docList[i + results_per_page * (page - 1)][0] + '''</a></ul>'''

    output += '''</div></div>'''

    #if interp != "def" and interp != "calc":
        #output += displayimages(docList, resultsOnCurrentPage, page, results_per_page)
    
    output += '''<div class="pages">
	<form id="switchPage" method="post">'''

    if page > 1: #i.e.: not on the first page
        output += '''<input name="prev" id="prev" type="submit" value="<<" class="btn"></input>'''
		
    if (page + 1) * results_per_page < len(docList): #i.e.: not on last page
        output += '''<input name="next" id="next" type="submit" value=">>" class="btn"></input>'''
	
    output += '''</form></div></section><body></html>'''

    return output

def singlePage(docList):
    global interp
    output = '''<div class="results">'''

    for i in range(len(docList)):
        #output += '''<ul><img src="camera.png" id="show_img"''' + str(i) + '''class="icon" onmouseover="document.getElementById('img_link''' + str(i) + '''').style.visibility = 'visible';" onmouseout="document.getElementById('img_link''' + str(i) + '''').style.visibility = 'hidden';"></img>'''
        output += '''<ul><a href="''' + docList[i][0] + '''">''' + docList[i][0] + '''</a></ul>'''

    output += '''</div></div>'''

    #if interp != "def" and interp != "calc":
        #output += displayimages(docList, len(docList), 1, 5)    

    output += '''</section><body></html>'''

    return output

def displayimages(docList, numToDisplay, page, results_per_page):
    output = str()

    for i in range(numToDisplay):
        if docList[i + results_per_page * (page - 1)][2] != "No images":
            output += '''<div class="images" id="img_link''' + str(i) + '''><br><img height="90%" src="'''+ docList[i + results_per_page * (page - 1)][2] + '''"></img><br><br></div>'''

    return output

@post('/results')
def changePage():
    global page
    global suggest
    global userInput
    global inputFromSuggestion

    if request.POST.get('next'): 
        page += 1
    elif request.POST.get('prev'):
        page -= 1
    else:
        for i in range(len(suggest)):
            if request.POST.get(suggest[i]):
                userInput = str(suggest[i])
                inputFromSuggestion = True
                break

        return getResults()
    return displayResults()

@error(404)
def error404(error):
    return '''
<html>
<head>
<style>
html { 
  background:  url(https://mir-s3-cdn-cf.behance.net/project_modules/disp/0efaf032676677.568ed0d61d000.gif) center center fixed; 
  background-size: 100% 100%;
  background-repeat: no-repeat;
  font-family: sans-serif;

}
h1{
  font-size: 12em;
  
  color: rgba(0,255,255, 0.8);
 
}
h3{
  font-size: 2em;
 
  color: rgba(255,255,255, 0.7);
	
}

div.page{
  position:absolute;
  top:20%;
  margin-top:-8em;
  width:90%;
  text-align:left;
}
</style>
<head>
<body>
<div class="page">
  <h4><a href="/">Back to main page</a></h4>
  <h3>OOPS! something went wrong...</h3>
</div>
</body>
</html>
''' 
    
#bottle.run(app=app)
run(host='localhost', port=8080, debug=True) #note: localhost:8080 is hardcoded into login/logout buttons (change this later if possible)
