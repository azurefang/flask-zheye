from datetime import datetime
from app import db


from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

from . import login_manager

question_followers = db.Table('question_followers',
        db.Column('question_id', db.Integer, db.ForeignKey('question.id')),
        db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
        )

topic_followers = db.Table('topic_followers',
        db.Column('topic_id', db.Integer, db.ForeignKey('topic.id')),
        db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
        )
answer_collectors = db.Table('answer_collectors',
        db.Column('answer_id', db.Integer, db.ForeignKey('answer.id')),
        db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
        )

question_topics = db.Table('question_topics',
        db.Column('question_id', db.Integer, db.ForeignKey('question.id')),
        db.Column('topic_id', db.Integer, db.ForeignKey('topic.id'))
        )

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(8))
    lastname = db.Column(db.String(10))
    password_hash = db.Column(db.String(128))
    domain = db.Column(db.String(30))
    email = db.Column(db.String(30), unique=True)
    about_me = db.Column(db.Text)
    member_since = db.Column(db.DateTime, default=datetime.utcnow())
    last_seen = db.Column(db.DateTime, default=datetime.utcnow())

    comment = db.relationship('Comment', backref='owner', lazy='dynamic')
    question = db.relationship('Question', backref='owner', lazy='dynamic')
    answer = db.relationship('Answer', backref='owner', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verity_password(self, password):
        return check_password_hash(self.password_hash, password)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def __repr__(self):
        return "<User {}>".format(self.domain)


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    followers = db.relationship('User', secondary=topic_followers, backref=db.backref('topics', lazy='dynamic'))

    def __repr__(self):
        return "<Topic:{}>".format(self.name)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30))
    time = db.Column(db.DateTime, default=datetime.utcnow())
    content = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    followers = db.relationship('User', secondary=question_followers, backref=db.backref('followed_questions', lazy='dynamic'))
    topics = db.relationship('Topic', secondary=question_topics, backref=db.backref('related_questions', lazy='dynamic'))
    answers = db.relationship('Answer', backref='quesion', lazy='dynamic')

    def __repr__(self):
        return "<Question:{}>".format(self.id)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, default=datetime.utcnow())
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    content = db.Column(db.Text)
    #liker
    #hater
    collectors = db.relationship('User', secondary=answer_collectors, backref=db.backref('collected_answers', lazy='dynamic'))

    comment = db.relationship('Comment', backref='answer', lazy='dynamic')

    def __repr__(self):
        return "<Answer:{}>".format(self.id)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, default=datetime.utcnow())
    content = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    #liker
    #father

