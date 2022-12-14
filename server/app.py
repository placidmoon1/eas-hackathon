from flask import Flask, render_template
from flask_cors import CORS
from config import app_secret_key
import datetime
import os
import auth

app = Flask(__name__)
app.secret_key = app_secret_key
cors = CORS(app)

@app.route('/')
def index():
  dummy_times = [datetime.datetime(2022, 1, 1, 10, 0, 0),
                  datetime.datetime(2022, 1, 2, 10, 30, 0),
                  datetime.datetime(2022, 1, 3, 11, 0, 0),
                  ]

  return render_template('index.html', times=dummy_times)

app.register_blueprint(auth.bp)

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))