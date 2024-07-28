from flask import Flask, send_file,render_template,request, jsonify
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug = True,host = '0.0.0.0')