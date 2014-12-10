import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'YOU CAN GUESS'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    ZHEYE_MAIL_SENDER = 'ZHEYE Admin <noreply@zheye.com>'
    ZHEYE_ADMIN = os.environ.get('ZHEYE_ADMIN')
    CACHE_CONFIG = {
        'CACHE_TYPE': 'redis',
    }
    CELERY_BROKER_URL = 'redis://localhost:6379',
    #CELERY_RESULT_BACKEND='redis://localhost:6379'
    CELERYBEAT_SCHEDULE = {
        'add-every-1-seconds': {
            'task': 'tasks.message_queue',
            'schedule': timedelta(seconds=5),
            #'args': (16, 16)
    },
}

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
    }
