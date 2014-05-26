from flask import render_template
from . import main

@main.route('/index')
def index():
    return render_template('index.html')


@main.route('/user/<domain>')
def user(domain):
    user = User.query.filter_by(domain=domain).first()
    if user is None:
        abort(404)
    return render_template('user.html', user=user)

