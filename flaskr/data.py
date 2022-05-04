import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from flaskr.auth import login_required, admin_required

import pandas as pd
from sqlalchemy.sql import select


bp = Blueprint('data', __name__, url_prefix='/data')

@bp.route('/chart', methods=('GET', 'POST'))
def chart():
    from flaskr.models import Article, Topic
    db = get_db()

    articles = pd.read_sql(db.query(Article).statement, db.bind)
    topics = pd.read_sql(db.query(Topic).statement, db.bind)

    articles = articles.join(topics.set_index('id'), how='left', on='topic_id', lsuffix='l', rsuffix='r')
    articles_by_topic = articles.groupby('name').count()

    return render_template('data/chart.html', type='bar', 
                            values=articles_by_topic['id'], labels=articles_by_topic.index, legend='Articles')

@bp.route('/articles', methods=('GET', 'POST'))
def articles():
    from flaskr.models import Article, Topic, Author
    db = get_db()

    articles = pd.read_sql(db.query(Article).statement, db.bind)
    topics = pd.read_sql(db.query(Topic).statement, db.bind)
    authors = pd.read_sql(db.query(Author).statement, db.bind)

    articles = articles.join(topics.set_index('id'), how='left', on='topic_id', lsuffix='l', rsuffix='r')
    articles = articles.join(authors.set_index('id'), how='left', on='author_id', lsuffix='l', rsuffix='r')
    
    heads_select=['day', 'namel', 'namer', 'wordcount']
    heads_repl = ['Publication Date', 'Topic', 'Author', 'Word Count']
    articles = articles[heads_select]
    articles = articles.rename(columns={i:j for i, j in zip(heads_select, heads_repl)})

    return render_template('data/table.html', table=articles)

@bp.route('/users', methods=('GET', 'POST'))
def users():
    from flaskr.models import User
    db = get_db()
    users = pd.read_sql(db.query(User).statement, db.bind)

    return render_template('data/table.html', table=users)

@bp.route('/pvs', methods=('GET', 'POST'))
def pvs():
    from flaskr.models import Pageview
    db = get_db()
    pvs = pd.read_sql(db.query(Pageview ).statement, db.bind)

    return render_template('data/table.html', table=pvs)