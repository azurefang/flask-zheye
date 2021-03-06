# coding:utf-8

from flask import render_template, redirect, abort, request, flash, Markup
from flask.ext.login import current_user, login_required
from sqlalchemy import desc
from . import main
from app import db, conn
from .forms import AskForm, AnswerForm
from ..models import User, Topic, Question, Answer, Activity


@main.route('/')
@main.route('/index')
@login_required
def index():
    if current_user.followed_questions.all()==current_user.followed_topics.all()==current_user.followed_users.all()==[]:
        message = Markup(u'你尚未有任何动态，试着第一次<a href="/ask">提问</a>')
        flash(message)
    activities = Activity.query.filter_by(user_id=current_user.id)
    for user in current_user.get_followed_users():
        activities.union(Activity.query.filter_by(user_id=user.id))
    page = request.args.get('page', 1, type=int)
    pagination = activities.order_by(desc(Activity.timestamp)).paginate(page, per_page=4)
    activities = pagination.items
    return render_template('index.html', activities=activities, pagination=pagination)


@main.route('/ask', methods=['POST', 'GET'])
@login_required
def ask():
    form = AskForm()
    if form.validate_on_submit():
        topics = request.form.get('hidden-topics').split(',')
        question = Question(
            title=form.title.data,
            content=form.content.data,
            anonymous=form.anonymous.data,
            owner_id=current_user.id)
        db.session.add(question)
        for i in topics:
            topic = Topic.query.filter_by(name=i).first()
            if topic is None:
                topic = Topic(name=i)
                db.session.add(topic)
                topic = topic
            question.add_topic(topic)
        current_user.follow_question(question)
        db.session.commit()
        activity = Activity(user_id=current_user.id, question_id=question.id, move=3)
        db.session.add(activity)
        db.session.commit()
        conn.lpush("message", "user" + str(current_user.id) + ":xx ask a new question")
        return redirect('/question/{}'.format(question.id))
    return render_template('ask_question.html', form=form)


@main.route('/question/<int:qid>', methods=['POST', 'GET'])
def question(qid):
    question = Question.query.filter_by(id=int(qid)).first()
    if question is None:
        abort(404)
    form = AnswerForm()
    if form.validate_on_submit():
        answer = Answer(
            owner_id=current_user.id,
            question_id=int(qid),
            content=form.content.data)
        db.session.add(answer)
        db.session.commit()
        activity = Activity(user_id=current_user.id, question_id=int(qid), answer_id=answer.id, move=1)
        db.session.add(activity)
        db.session.commit()
        flash('thank you')
        return redirect('/question/{}'.format(qid))
    return render_template('display_question.html', question=question, form=form)


@main.route('/user/<uid>')
def user(uid):
    user = User.query.filter_by(id=uid).first()

    if user is None:
        abort(404)
    return render_template('display_user.html', user=user)


@main.route('/topic/<int:tid>')
def topic(tid):
    topic = Topic.query.filter_by(id=tid).first()
    if topic is None:
        abort(404)
    return render_template('display_topic.html', topic=topic)
