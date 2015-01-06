# coding:utf-8

from flask import request, json, Response
from flask.ext.login import current_user

from ..models import User, Topic, Question, Activity, Answer
from . import ajax
from app import db


@ajax.route('/relationship', methods=['POST', 'GET'])
def relationship():
    if request.method == 'GET':
        type = request.args.get('type', '')
        id = request.args.get('id', '')
        if type == 'user':
            if current_user.is_following_user(User.query.get(int(id))):
                return '取消关注'
            else:
                return '关注'
        if type == 'topic':
            if current_user.is_following_topic(Topic.query.get(int(id))):
                return '取消关注'
            else:
                return '关注'
        if type == 'question':
            if current_user.is_following_question(Question.query.get(int(id))):
                return '取消关注'
            else:
                return '关注'

    if request.method == 'POST':
        type = request.form.get('type')
        id = request.form.get('id')
        if type == 'user':
            user = User.query.get(int(id))
            if current_user.is_following_user(user):
                current_user.unfollow_user(user)
            else:
                current_user.follow_user(user)
        if type == 'topic':
            topic = Topic.query.get(int(id))
            if current_user.is_following_topic(topic):
                current_user.unfollow_topic(topic)
            else:
                current_user.follow_topic(topic)
                new_activity = Activity(user_id=current_user.id, topic_id=topic.id, move=4)
                db.session.add(new_activity)
        if type == 'question':
            question = Question.query.get(int(id))
            if current_user.is_following_question(question):
                current_user.unfollow_question(question)
            else:
                current_user.follow_question(question)
                new_activity = Activity(user_id=current_user.id, question_id=id, move=2)
                db.session.add(new_activity)
        db.session.commit()
        return 'success'


@ajax.route('/topic')
def topic():
    all_topics = [i.name for i in Topic.query.all()]
    result = json.dumps(all_topics)
    return Response(result, mimetype='application/json')


@ajax.route('/messages')
def messages():
    if request.method == 'GET':
        messages = [message.content for message in current_user.get_unread_messages()]
        return Response(json.dumps(messages), mimetype='application/json')


@ajax.route('/collect')
def collect():
    if request.method == 'GET':
        id = request.args.get('id', '')
        if current_user.is_collecting_answer(Answer.query.get(int(id))):
            return u'取消收藏'
        else:
            return u'收藏'
