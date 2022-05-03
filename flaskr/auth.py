import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from flaskr.models import Player

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        gameid = request.form['gameid']
        name = request.form['teamName']
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif not name:
            error = 'Team name is required.'
        elif not gameid:
            error = 'Game ID is required.'

        if error is None:
            try:
                new_player = Player(email=email, password=password, name=name, type='student', status='pending')
                db.add(new_player)
                db.commit()
            except:
                pass
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')
    
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.query(Player).filter(Player.email == username).first()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            acct_type = user.type
            confirm = 0
            if user.status == 'confirmed':
                confirm = 1
            if confirm == 1:
                if acct_type == 'student':
                    return redirect('/home')
                elif acct_type == 'admin':
                    return redirect('/admin')
            elif confirm == 0:
                error = 'Your account must be activated before you can login.'

        flash(error)

    return render_template('auth/login.html')
    
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        db = get_db()
        user = db.query(Player).filter(Player.id == user_id).first()
        g.user = user
             
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
    
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
    
def admin_required(view):
    @functools.wraps(view)
    @login_required
    def wrapped_view(**kwargs):
        print(g.user)
        if g.user.type != 'admin':
            return redirect(url_for('auth.login'))
            
        return view(**kwargs)
    
    return wrapped_view
    
@bp.route('/register-admin', methods=('GET', 'POST'))
@admin_required
def registerAdmin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                new_admin = Player(email=email, password=password, type='admin', status='confirmed')
                db.add(new_admin)
                db.commit()
            except:
                pass
            else:
                return redirect(url_for("auth.login"))

    return render_template('auth/register-admin.html')