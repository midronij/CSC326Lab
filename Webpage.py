from bottle import route, run, get, post, request, response, template
@get('/')
def hello():
   response.delete_cookie("keywords")
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
		height: 30px;
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
	 <input name="keywords" id="keywords" type="text" placeholder="Enter your Phrase"/><br><br><input id="submit" type="submit" value="Search" class="btn"></input>
	 </form>
	 </section>
	</html>
'''

@post('/')
def displayResults():

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
	output = "<h2>Search Results</h2><table name=\"results\"><tr><th>Word</th><th>Count</th><tr>"
	
        #add a row to the results table for each word the user has entered
	for key, value in dictionary.iteritems():
	    output += "<tr><td>" + key + "</td><td> &nbsp;&nbsp;&nbsp;&nbsp;" + str(value) + "</td></tr>"
        
        output += "</table>"

        #top 20 keywords table
        keywords = str()

        if "keywords" not in request.cookies: #create the cookie if it doesn't already exist (stored as string of every word the user has entered
            keywords = userInput + " "
        else:
            keywords = str(request.get_cookie("keywords")) + userInput + " "

        response.set_cookie("keywords", keywords) #update the cookie with newly entered keywords
        
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

run(host='localhost', port=8090, debug=True)
