from celery import Celery
from manage import app
from app.models import Message, User
from app import db, conn
import time

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


celery = make_celery(app)

@celery.task()
def push_message(user_id, content):
    message = Message(user_id = user_id, content=content)
    db.session.add(message)
    db.session.commit()


@celery.task()
def message_queue():
    with app.app_context():
        for item in conn.lrange("message", 0, -1):
            user_info, content = item.split(':')
            user = User.query.filter_by(id = user_info[4:]).first()
            for receiver in user.followers:
                push_message.delay(receiver.id, content)
            conn.rpop("message")

