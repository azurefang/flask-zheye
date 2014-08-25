# -*- coding:utf-8 -*-
import sys
from flask import request, json, jsonify, Response
from . import ajax
from flask.ext.login import current_user
from ..models import *
from app import db

@ajax.route('/relationship', methods=['POST', 'GET'])
def relationship():
    if request.method == 'GET':
        type = request.args.get('type', '')
        id = request.args.get('id', '')
        if type=='user':
            if current_user.is_following_user(User.query.filter_by(id=int(id)).first()):
                return '取消关注'
            else:
                return '关注'
        if type == 'topic':
            if current_user.is_following_topic(Topic.query.filter_by(id=int(id)).first()):
                return '取消关注'
            else:
                return '关注'
        if type == 'question':
            id = int(id) - 19550224
            if current_user.is_following_question(Question.query.filter_by(id=id).first()):
                return '取消关注'
            else:
                return '关注'

    if request.method == 'POST':
        type = request.form.get('type')
        id = request.form.get('id')
        if type=='user':
            user = User.query.filter_by(id=int(id)).first()
            if current_user.is_following_user(user):
                current_user.followed.remove(user)
            else:
                current_user.followed.append(user)
        if type == 'topic':
            topic = Topic.query.filter_by(id=int(id)).first()
            if current_user.is_following_topic(topic):
                current_user.followed_topics.remove(topic)
            else:
                current_user.followed_topics.append(topic)
                new_activity = Activity(user_id=current_user.id, topic_id=topic.id, move=4)
                db.session.add(new_activity)
        if type == 'question':
            id = int(id) - 19550224
            question = Question.query.filter_by(id=id).first()
            if current_user.is_following_question(question):
                current_user.followed_questions.remove(question)
            else:
                current_user.followed_questions.append(question)
                new_activity = Activity(user_id=current_user.id, question_id=id, move=2)
                db.session.add(new_activity)
        db.session.commit()

        return 'success'

@ajax.route('/topic')
def topic():
    all_topics = [i.name for i in Topic.query.all()]
    result = json.dumps(all_topics)
    return Response(result, mimetype='application/json')
