# coding:utf-8

from datetime import datetime

from flask import current_app
from flask.ext.login import UserMixin

from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, cache


class Permission:
    FOLLOW = 0x01
    ANSWER = 0x02
    ASK = 0x04
    MODERATE = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.ANSWER |
                     Permission.ASK, True),
            'Manager': (Permission.FOLLOW |
                        Permission.ANSWER |
                        Permission.ASK |
                        Permission.MODERATE, False),
            'Admin': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).firt()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role:{}>'.format(self.name)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class UserFollower(db.Model):
    __tablename__ = 'userfollowers'
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())


class QuestionFollower(db.Model):
    __tablename__ = 'questionfollowers'
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), primary_key=True)
    question_id = db.Column(
        db.Integer, db.ForeignKey('questions.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())


class TopicFollower(db.Model):
    __tablename__ = 'topicfollowers'
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), primary_key=True)
    topic_id = db.Column(
        db.Integer, db.ForeignKey('topics.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())


class AnswerCollector(db.Model):
    __tablename__ = 'answercollectors'
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), primary_key=True)
    answer_id = db.Column(
        db.Integer, db.ForeignKey('answers.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())


class QuestionTopic(db.Model):
    __tablename__ = 'questiontopics'
    question_id = db.Column(
        db.Integer, db.ForeignKey('questions.id'), primary_key=True)
    topic_id = db.Column(
        db.Integer, db.ForeignKey('topics.id'), primary_key=True)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(30), unique=True, index=True)
    about_me = db.Column(db.Text)
    member_since = db.Column(db.DateTime, default=datetime.utcnow())
    last_seen = db.Column(db.DateTime, default=datetime.utcnow())
    confirmed = db.Column(db.Boolean, default=False)
    followed_users = db.relationship('UserFollower',
                                     foreign_keys=[UserFollower.user_id],
                                     backref=db.backref(
                                         'follower', lazy='joined'),
                                     lazy='dynamic',
                                     cascade='all, delete-orphan')
    followed_questions = db.relationship('QuestionFollower',
                                         foreign_keys=[
                                             QuestionFollower.user_id],
                                         backref=db.backref(
                                             'follower', lazy='joined'),
                                         lazy='dynamic',
                                         cascade='all, delete-orphan')
    followed_topics = db.relationship('TopicFollower',
                                      foreign_keys=[TopicFollower.user_id],
                                      backref=db.backref(
                                          'follower', lazy='joined'),
                                      lazy='dynamic',
                                      cascade='all, delete-orphan')
    followers = db.relationship('UserFollower',
                                foreign_keys=[UserFollower.followed_id],
                                backref=db.backref(
                                    'followed_user', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    collected_answers = db.relationship('AnswerCollector',
                                        foreign_keys=[AnswerCollector.user_id],
                                        backref=db.backref(
                                            'collector', lazy='joined'),
                                        lazy='dynamic',
                                        cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='owner', lazy='dynamic')
    questions = db.relationship('Question', backref='owner', lazy='dynamic')
    answers = db.relationship('Answer', backref='owner', lazy='dynamic')
    activity = db.relationship('Activity', backref='owner', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['ZHEYE_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            else:
                self.role = Role.query.filter_by(default=True).first()

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

    def follow_user(self, user):
        if not self.is_following_user(user):
            f = UserFollower(follower=self, followed_user=user)
            db.session.add(f)

    def unfollow_user(self, user):
        f = self.followed_users.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def follow_topic(self, topic):
        if not self.is_following_topic(topic):
            f = TopicFollower(follower=self, followed_topic=topic)
            db.session.add(f)

    def unfollow_topic(self, topic):
        f = self.followed_topics.filter_by(topic_id=topic.id).first()
        if f:
            db.session.delete(f)

    def follow_question(self, question):
        if not self.is_following_question(question):
            f = QuestionFollower(follower=self, followed_question=question)
            db.session.add(f)

    def unfollow_question(self, question):
        f = self.followed_questions.filter_by(question_id=question.id).first()
        if f:
            db.session.delete(f)

    def collect_answer(self, answer):
        if not self.is_collecting_answer(answer):
            c = AnswerCollector(collector=self, collected_answer=answer)
            db.session.add(c)

    def uncollect_answer(self, answer):
        c = self.collected_answers.filter_by(answer_id=answer.id).first()
        if c:
            db.session.delete(c)

    def is_followed_by(self, user):
        return self.followers.filter_by(user_id=user.id).first() is not None

    def is_following_user(self, user):
        return self.followed_users.filter_by(followed_id=user.id).first() is not None

    def is_following_topic(self, topic):
        return self.followed_topics.filter_by(topic_id=topic.id).first() is not None

    def is_following_question(self, question):
        return self.followed_questions.filter_by(question_id=question.id).first() is not None

    def is_collecting_answer(self, answer):
        return self.collected_answers.filter_by(answer_id=answer.id).first() is not None

    def get_followed_users(self):
        return [rel.follower for rel in self.followed_users]

    def get_followers(self):
        return [rel.follower for rel in self.followers]

    def __repr__(self):
        return "<User:{}>".format(self.username)


class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    desc = db.Column(db.Text)
    followers = db.relationship('TopicFollower',
                                foreign_keys=[TopicFollower.topic_id],
                                backref=db.backref(
                                    'followed_topic', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    questions = db.relationship('QuestionTopic',
                                foreign_keys=[QuestionTopic.topic_id],
                                backref=db.backref(
                                    'topic', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    activity = db.relationship('Activity', backref='topic', lazy='dynamic')

    def get_followers(self):
        return [rel.follower for rel in self.followers]

    def get_questions(self):
        return [rel.question for rel in self.questions]

    def __repr__(self):
        return "<Topic:{}>".format(self.name)


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    anonymous = db.Column(db.Boolean)
    followers = db.relationship('QuestionFollower',
                                foreign_keys=[QuestionFollower.question_id],
                                backref=db.backref(
                                    'followed_question', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    topics = db.relationship('QuestionTopic',
                             foreign_keys=[QuestionTopic.question_id],
                             backref=db.backref(
                                 'question', lazy='joined'),
                             lazy='dynamic',
                             cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='question', lazy='dynamic')
    activity = db.relationship('Activity', backref='question', lazy='dynamic')

    def has_topic(self, topic):
        return self.topics.filter_by(topic_id=topic.id).first() is not None

    def add_topic(self, topic):
        if not self.has_topic(topic):
            r = QuestionTopic(question=self, topic=topic)
            db.session.add(r)

    def remove_topic(self, topic):
        c = self.topics.filter_by(topic_id=topic.id).first()
        if c:
            db.session.delete(c)

    def get_topics(self):
        return [rel.topic for rel in self.topics]

    def __repr__(self):
        return "<Question:{}>".format(self.id)


class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    content = db.Column(db.Text)
    activity = db.relationship('Activity', backref='answer', lazy='dynamic')
    collectors = db.relationship('AnswerCollector',
                                 foreign_keys=[AnswerCollector.answer_id],
                                 backref=db.backref(
                                     'collected_answer', lazy='joined'),
                                 lazy='dynamic',
                                 cascade='all, delete-orphan')

    comment = db.relationship('Comment', backref='answer', lazy='dynamic')

    def __repr__(self):
        return "<Answer:{}>".format(self.id)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())
    content = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))

    def __repr__(self):
        return "<Comment:{}>".format(self.id)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    '''
    1:answer question;2:follow question;3:ask question;4:follow topic
    '''
    move = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'))
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    read = db.Column(db.Boolean, default=False)
    content = db.Column(db.Text)

    def __repr__(self):
        return "<Message:{}>".format(self.id)
