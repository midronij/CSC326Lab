from bottle import route, run, get, post, request, template
@get('/')
def hello():
   return '''
	<html>

	<head>
		<title>Test site</title>
	</head>

	<body>

		<h1>Testing</h1>
		<p>This website is for testing purposes.</p>

	</body>

	</html>

'''
run(host='localhost', port=8080, debug=True)
