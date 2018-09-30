from bottle import route, run, get, post, request, template
@get('/')
def hello():
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
	 <input name="phrase" id="phrase" placeholder="Enter your Phrase"/><br><br><input id="submit" type="submit" value="Search" class="btn"></input>
	 </form>
	 </section>
	</html>
'''

@post('/')
def displayResults():

	userInput = request.forms.get('phrase')

	words = userInput.split()
	dictionary = {}

	for x in words:
		if dictionary.has_key(x):
			dictionary[x] += 1
		else:
			dictionary[x] = 1
	
	output = "<h2>Search Results</h2><table><tr><th>Word</th><th>Count</th><tr>"
	
	for key, value in dictionary.iteritems():
		output += "<tr><td>" + key + "</td><td> &nbsp;&nbsp;&nbsp;&nbsp;" + str(value) + "</td></tr>"

	return output
run(host='localhost', port=8080, debug=True)
