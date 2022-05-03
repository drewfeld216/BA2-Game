import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from flaskr.auth import login_required, admin_required

import pandas as pd

bp = Blueprint('data', __name__, url_prefix='/data')

@bp.route('/chart', methods=('GET', 'POST'))
def chart():
    legend = 'Monthly Data'
    labels = ["January", "February", "March", "April", "May", "June", "July", "August"]
    values = [10, 9, 8, 7, 6, 4, 7, 8]
    return render_template('data/chart.html', values=values, labels=labels, legend=legend)

@bp.route('/articles', methods=('GET', 'POST'))
def articles():
    from flaskr.models import Article
    db = get_db()
    articles = db.query(Article)
    heads = list(articles[0].__dict__.keys())
    print(heads)
    return render_template('data/table.html', values=articles, headers=heads)

@bp.route('/users', methods=('GET', 'POST'))
def users():
    from flaskr.models import User
    db = get_db()
    users = db.query(User)
    heads = list(users[0].__dict__.keys())
    print(heads)
    return render_template('data/table.html', values=users, headers=heads)

@bp.route('/pvs', methods=('GET', 'POST'))
def pvs():
    from flaskr.models import Pageview
    db = get_db()
    pvs = db.query(Pageview)
    heads = list(pvs[0].__dict__.keys())
    print(heads)
    return render_template('data/table.html', values=pvs, headers=heads)