# coding:utf-8

from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, BooleanField, TextField, TextAreaField
from wtforms.validators import Required


class AskForm(Form):
    title = StringField(u'标题', validators=[Required()])
    topics = TextField(u'话题', id='choose')
    content = TextAreaField(u'题干', validators=[Required()])
    anonymous = BooleanField(u'匿名', default=False)
    submit = SubmitField(u'提问')


class AnswerForm(Form):
    content = TextAreaField(id="editor", validators=[(Required())])
    submit = SubmitField(u'提交')
