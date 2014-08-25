# -*- coding:utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, BooleanField, TextField, TextAreaField
from wtforms.validators import Required


class AskForm(Form):
    title = StringField('title', validators=[Required()])
    topics = TextField('topic', id='choose')
    content = TextAreaField('content', validators=[Required()])
    anonymous = BooleanField('匿名', default=False)
    submit = SubmitField('提问')


class AnswerForm(Form):
    content = TextAreaField(id="editor", validators=[(Required())])
    submit = SubmitField('提交')
