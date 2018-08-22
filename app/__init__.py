import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from celery import Celery

app = Flask(__name__)
app.config.from_object(os.environ["APP_SETTINGS"])

db = SQLAlchemy(app)
migrate = Migrate(app, db)

celery = Celery(app.name)
celery.conf.update(
    BROKER_URL=app.config["BROKER_URL"],
    CELERY_RESULT_BACKEND=app.config["CELERY_RESULT_BACKEND"]
)

login_manager = LoginManager(app)

from app import views, models, tasks
