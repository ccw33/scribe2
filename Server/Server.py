import json

from flask import Flask,render_template,Response,request

app = Flask(__name__,static_folder='static',template_folder='dist')

app.debug=True

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/get_new_ip_port',methods=['GET'])
def get_lans_data():
    a = request.args['uuid']
    return Response('accepted')

if __name__ == '__main__':
    app.run()
