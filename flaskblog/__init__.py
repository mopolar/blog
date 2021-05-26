import datetime
from logging.config import dictConfig
from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flaskext.markdown import Markdown
from sqlalchemy import event
import os


dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] [%(levelname)s] [%(name)s] [%(module)s:%(lineno)s] - %(message)s',
    }},
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        },
        'to_file': {
                'level': 'DEBUG',
                'formatter': 'default',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'messages.log',
                'maxBytes': 5000000,
                'backupCount': 10
            },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'to_file']
    }
})

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL1')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False  # option for debugging -- should be set to False for production

db = SQLAlchemy(app)


# this function makes apis accessible only for the requests with valid tokens
@app.before_request
def before():
    if request.path.startswith('/api') \
            and request.path != '/api/token/public':
        if request.is_json and 'Authorization' in request.headers: # only JSON requests are allowed
            from flaskblog.models import Token
            token_string = request.headers['Authorization'].split(' ')[1]
            token = Token.query.filter_by(token=token_string).all()
            now = datetime.datetime.now()
            if len(token) == 0:
                abort(403)
            elif token[0].date_expired < now:
                abort(403)
        else:
            return abort(403)


bcrypt = Bcrypt(app)
Markdown(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from flaskblog import routes
from flaskblog import routesapi
