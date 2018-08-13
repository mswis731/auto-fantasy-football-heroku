import os

class Config(object):
    DEBUG = False
    SECRET_KEY = os.environ["APP_SECRET_KEY"]

class ProductionConfig(Config):
    DEBUG = True
    GOOGLE_CHROME_BIN = "/app/.apt/usr/bin/google-chrome-stable"
    CHROMEDRIVER_PATH =  "/app/.chromedriver/bin/chromedriver"

class DevelopmentConfig(Config):
    DEBUG = True
    GOOGLE_CHROME_BIN = "/usr/bin/google-chrome-stable"
    CHROMEDRIVER_PATH =  "/usr/local/bin/chromedriver"
