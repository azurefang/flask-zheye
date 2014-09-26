from flask.ext.login import current_user
from flask.ext.socketio import emit, send
from .. import socketio


@socketio.on('text')
def handle_my_custom_event(message):
    for i in current_user.pubsub.listen():
        emit('message', i)
