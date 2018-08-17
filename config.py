import os

class Config(object):
    DEBUG = False
    SECRET_KEY = os.environ["APP_SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BROKER_URL = os.environ["REDIS_URL"]
    CELERY_RESULT_BACKEND = os.environ["REDIS_URL"]

class ProductionConfig(Config):
    DEBUG = True
    GOOGLE_CHROME_BIN = "/app/.apt/usr/bin/google-chrome-stable"
    CHROMEDRIVER_PATH =  "/app/.chromedriver/bin/chromedriver"

class DevelopmentConfig(Config):
    DEBUG = True
    GOOGLE_CHROME_BIN = "/usr/bin/google-chrome-stable"
    CHROMEDRIVER_PATH =  "/usr/local/bin/chromedriver"
