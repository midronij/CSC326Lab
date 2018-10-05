from bottle import route, run, get, post, request, template
@get('/')
def hello():
   return '''
	<html>

	<head>
		<title>Test site2</title>
	</head>

	<body>

		<p>Another site for testing</p>

	</body>

	</html>

'''
run(host='localhost', port=8000, debug=True)
