import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from create import *

#app decorator
app = Flask(__name__)

#config for celery
app.config.update(
	CELERY_BROKER_URL = 'redis://localhost:6379/0',
	CELERY_RESULT_BACKEND = 'redis://localhost:6379/0',
)

app.config.from_object('config')

#celery = create_celery(app)

#database
db = SQLAlchemy(app)

#login
lm = LoginManager()
lm.init_app(app)
lm.login_views = 'login'

from app import views, models


