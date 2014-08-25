# -*- coding:utf-8 -*-
from flask import render_template, redirect, abort, request, flash, Markup
from flask.ext.login import current_user, login_required
from sqlalchemy import desc
from . import main
from app import db
from .forms import AskForm, AnswerForm
from ..models import *

@main.route('/')
@main.route('/index')
@login_required
def index():
    if current_user.followed_questions.all()==current_user.followed_topics.all()==current_user.followed_users.all()==[]:
        message = Markup('你尚未有任何动态，试着第一次<a href="/ask">提问</a>')
        flash(message)
    activities = Activity.query.filter_by(user_id=current_user.id)
    for user in current_user.followed:
        activities.union(Activity.query.filter_by(user_id=user.id))
    page = request.args.get('page', 1, type=int)
    pagination = activities.order_by(desc(Activity.time)).paginate(page, per_page=4)
    activities = pagination.items
    return render_template('index.html', activities=activities, pagination=pagination)

@main.route('/user/<domain>')
def user(domain):
    user = User.query.filter_by(domain=domain).first()

    if user is None:
        abort(404)
    return render_template('user.html', user=user)


@main.route('/ask', methods=['POST', 'GET'])
@login_required
def ask():
    form = AskForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        anonymous = form.anonymous.data
        owner_id = current_user.id
        topics = request.form.get('hidden-topics').split(',')
        new_question = Question(title=title, content=content, anonymous=anonymous, owner_id=owner_id)
        db.session.add(new_question)
        for i in topics:
            topic = Topic.query.filter_by(name=i).first()
            if topic == None:
                new_topic = Topic(name=i)
                db.session.add(new_topic)
                topic = new_topic
            new_question.topics.append(topic)
        new_question.followers.append(current_user)
        db.session.commit()
        new_activity = Activity(user_id=owner_id, question_id=new_question.id, move=3)
        db.session.add(new_activity)
        db.session.commit()
        return redirect('/question/{}'.format(new_question.id+19550224))
    return render_template('ask_question.html', form=form)


@main.route('/question/<int:qid>', methods=['POST', 'GET'])
def question(qid):
    question = Question.query.filter_by(id=int(qid)-19550224).first()
    if question == None:
        abort(404)
    form = AnswerForm()
    if form.validate_on_submit():
        content = form.content.data
        new_answer = Answer(owner_id=current_user.id, question_id=int(qid)-19550224,content=content)
        db.session.add(new_answer)
        db.session.commit()
        new_activity = Activity(user_id=current_user.id, question_id=int(qid)-19550224, answer_id=new_answer.id, move=1)
        db.session.add(new_activity)
        db.session.commit()
        flash('thank you')
        return redirect('/question/{}'.format(qid))
    return render_template('display_question.html', question=question, form=form)


@main.route('/people/<int:pid>')
def people(pid):
    user = User.query.filter_by(id=pid).first()
    return render_template('display_user.html', user=user)

@main.route('/topic/<int:tid>')
def topic(tid):
    topic = Topic.query.filter_by(id=tid).first()
    return render_template('display_topic.html', topic=topic)
