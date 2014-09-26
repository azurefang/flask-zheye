from datetime import datetime
from app import db, conn
from flask import current_app
import forgery_py


from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

from . import login_manager

question_followers = db.Table('question_followers',
                              db.Column(
                                  'question_id', db.Integer, db.ForeignKey('question.id')),
                              db.Column(
                                  'user_id', db.Integer, db.ForeignKey('user.id'))
                              )

topic_followers = db.Table('topic_followers',
                           db.Column(
                               'topic_id', db.Integer, db.ForeignKey('topic.id')),
                           db.Column(
                               'user_id', db.Integer, db.ForeignKey('user.id'))
                           )
answer_collectors = db.Table('answer_collectors',
                             db.Column(
                                 'answer_id', db.Integer, db.ForeignKey('answer.id')),
                             db.Column(
                                 'user_id', db.Integer, db.ForeignKey('user.id'))
                             )

question_topics = db.Table('question_topics',
                           db.Column(
                               'question_id', db.Integer, db.ForeignKey('question.id')),
                           db.Column(
                               'topic_id', db.Integer, db.ForeignKey('topic.id'))
                           )

user_followers = db.Table('user_followers',
                          db.Column(
                              'user_id', db.Integer, db.ForeignKey('user.id')),
                          db.Column(
                              'follower_id', db.Integer, db.ForeignKey('user.id'))
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
    confirmed = db.Column(db.Boolean, default=False)

    comment = db.relationship('Comment', backref='owner', lazy='dynamic')
    question = db.relationship('Question', backref='owner', lazy='dynamic')
    answer = db.relationship('Answer', backref='owner', lazy='dynamic')
    followers = db.relationship('User', secondary=user_followers, primaryjoin=id == user_followers.c.user_id,
                                secondaryjoin=id == user_followers.c.follower_id, backref=db.backref('followed_users', lazy='dynamic'))
    followed = db.relationship('User', secondary=user_followers, primaryjoin=id == user_followers.c.follower_id,
                               secondaryjoin=id == user_followers.c.user_id, backref=db.backref('fans', lazy='dynamic'))
    activity = db.relationship('Activity', backref='owner', lazy='dynamic')

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

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def __repr__(self):
        return "<User {}>".format(self.domain)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following_user(self, user):
        return user in self.followed

    def is_followed_by(self, user):
        return self in user.followed

    def is_following_topic(self, topic):
        return topic in self.followed_topics.all()

    def is_following_question(self, question):
        return question in self.followed_questions.all()

    @staticmethod
    def generate_fake(count=100):
        #from sqlalchemy.ext import IntegrityError
        from random import seed

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                    firstname=forgery_py.internet.user_name(),
                    lastname=forgery_py.internet.first_name(),
                    password=forgery_py.lorem_ipsum.word(),
                    member_since=forgery_py.date.date(True),
                    )
            db.session.add(u)
            db.session.commit()



class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    followers = db.relationship('User', secondary=topic_followers, backref=db.backref(
        'followed_topics', lazy='dynamic'))
    activity = db.relationship('Activity', backref='topic', lazy='dynamic')

    def __repr__(self):
        return "<Topic:{}>".format(self.name)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30))
    time = db.Column(db.DateTime, default=datetime.utcnow())
    content = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    anonymous = db.Column(db.Boolean)
    followers = db.relationship('User', secondary=question_followers, backref=db.backref(
        'followed_questions', lazy='dynamic'))
    topics = db.relationship('Topic', secondary=question_topics, backref=db.backref(
        'related_questions', lazy='dynamic'))
    answers = db.relationship('Answer', backref='quesion', lazy='dynamic')

    activity = db.relationship('Activity', backref='question', lazy='dynamic')

    def __repr__(self):
        return "<Question:{}>".format(self.id)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, default=datetime.utcnow())
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    content = db.Column(db.Text)
    activity = db.relationship('Activity', backref='answer', lazy='dynamic')
    # liker
    # hater
    collectors = db.relationship('User', secondary=answer_collectors, backref=db.backref(
        'collected_answers', lazy='dynamic'))

    comment = db.relationship('Comment', backref='answer', lazy='dynamic')

    def __repr__(self):
        return "<Answer:{}>".format(self.id)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, default=datetime.utcnow())
    content = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    # liker
    # father


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    '''
    1:answer question;2:follow question;3:ask question;4:follow topic
    '''
    move = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    time = db.Column(db.DateTime, default=datetime.utcnow())


class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    read = db.Column(db.Boolean, default=False)
    content = db.Column(db.Text)
