import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    DEBUG = False
    TESTING = False
    API_VERSION = '1.0.0'
    APP_NAME = 'CrisisFeed Early Warning System'

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    TESTING = True
    DEBUG = True

config_map = {'development': DevelopmentConfig, 'production': ProductionConfig, 'testing': TestingConfig}

def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
