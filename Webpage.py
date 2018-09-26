from bottle import route, run
@route('/')
def hello():
   return "CSC326 Lab 1"
run(host='localhost', port=8080, debug=True)
