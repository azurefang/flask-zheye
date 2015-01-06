# coding:utf-8

from flask import render_template, redirect, abort, request, flash, Markup, session, url_for
from flask.ext.login import current_user, login_required
from flask.ext.socketio import emit, send, join_room
from sqlalchemy import desc
from . import main
from app import db, conn, socketio
from .forms import AskForm, AnswerForm
from ..models import User, Topic, Question, Answer, Activity, Message


@main.route('/')
@main.route('/index')
@login_required
def index():
    if current_user.followed_questions.all()==current_user.followed_topics.all()==current_user.get_followed_users()==[]:
        message = Markup(u'你尚未有任何动态，试着第一次<a href="/ask">提问</a>')
        flash(message)
    print current_user
    activities = Activity.query.filter_by(user_id=current_user.id)
    for user in current_user.get_followed_users():
        activities = activities.union(Activity.query.filter_by(user_id=user.id))
    page = request.args.get('page', 1, type=int)
    pagination = activities.order_by(desc(Activity.timestamp)).paginate(page, per_page=10)
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


@main.route('/user/<int:uid>')
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


@socketio.on('collect_answer')
def collect_answer(message):
    path = message['path']
    question_id = int(path.split('/')[2])
    answer_id = int(message['id'])
    print answer_id
    question = Question.query.get(question_id)
    answer = Answer.query.get(answer_id)
    content = u'<a href="{user_url}">{user}</a>收藏了你在<a href="{question_url}">{question}</a>下的回答'.format(
        user=current_user.username,
        user_url=url_for('main.user', uid=current_user.id),
        question_url=url_for('main.question', qid=question_id),
        question=question.title,
    )
    message = Message(content=content)
    answer.owner.add_message(message)
    db.session.add(message)
    message_count = len(answer.owner.get_unread_messages())
    session['message_count'] = message_count + 1
    #emit('join', {'room': 'user:' + str(current_user.id)})
    emit('count', {"data": session['message_count']}, room='user:' + str(answer.owner_id))
    answer = Answer.query.get(answer_id)
    current_user.collect_answer(answer)


@main.route('/unread')
def unread():
    for message in current_user.messages.filter_by(unread=True):
        message.unread = False
        db.session.add(message)
    return render_template('unread.html', topic=topic)


@main.route('/collections')
def collections():
    return render_template('collections.html', topic=topic)


@socketio.on('join')
def join(message):
    join_room(message['room'])

