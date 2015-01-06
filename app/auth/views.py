#  coding:utf-8

from flask import render_template, redirect, url_for, request, flash, abort, current_app
from flask.ext.login import login_user, logout_user, login_required, current_user
from flask.ext.socketio import join_room, leave_room, emit

from . import auth
from ..email import send_mail
from ..models import User
from .forms import LoginForm, RegistrationForm
from app import db, conn, cache, socketio


@auth.before_app_request
def before_request():
    if current_user.is_authenticated():
        current_user.ping()
        '''
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))
        '''


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verity_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash(u'欢迎回来')
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        '''
        token = user.generate_confirmation_token()
        send_mail(user.email, 'confirm your account', 'auth/email/confirm', user=user, token=token)
        flash('confirm email')
        '''
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account')
    else:
        flash('The confirmation link is in valid or has expired.')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_mail(current_user.email, 'confirm your account', 'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation link is in valid or has expired.')
    return redirect(url_for('main.index'))


@auth.route('/unconfirmed')
def unconfirmed():
    '''
    if current_user.is_anonymous():
        return redirect(url_for('main.index'))
    if current_user.confirmed:
        abort(404)
    '''
    if current_user.is_anonymous() or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')
