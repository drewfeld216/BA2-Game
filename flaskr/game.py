import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from flaskr.auth import login_required, admin_required
from flaskr.functions.simulate import seed, generate_pvs

bp = Blueprint('game', __name__, url_prefix='/game')

@bp.route('/create', methods=('GET', 'POST'))
@admin_required
def create():
    return render_template('game/create-game.html')
    
def register_game(game_name, rand_seed, n_days):
    admin = g.user.id
    db = get_db()
    
    error = None

    if not game_name:
        error = 'Name is required.'

    if not rand_seed:
        rand_seed = 123

    if not n_days:
        n_days = 10

    if error is None:
        try:
            seed(game_name, rand_seed)
            generate_pvs(0, int(n_days))
            db.commit()
        except:
            error = f"Game {game_name} has already been created."
        else:
            return redirect('/admin')

    return
    
@bp.route('game-list', methods=('GET', 'POST'))
@admin_required
def game_list():
    from flaskr.models import Game
    admin = g.user.id
    db = get_db()
    
    try:
        games = db.query(Game)
        game_info = [(game.name, game.id) for game in games]
        return game_nav_html(game_info)
    except:
        return
        
def game_nav_html(game_info):
    count = 0
    out = '<ul class="nav flex-column">' + '\n'
    for game in game_info:
        out += '    <li class="nav-item">' + '\n'
        if count == 0:
            out += '        <a class="nav-link side-link active" id="game-' + str(game[1]) + '" href="user/confirmed?game=' + str(game[1]) + '">' + '\n'
        else:
            out += '        <a class="nav-link side-link" id="game' + str(game[1]) + '" href="user/confirmed?game=' + str(game[1]) + '">' + '\n'
        out += '                ' + str(game[0]) + '\n'
        out += '        </a>' + '\n'
        out += '    </li>' + '\n' 
        count += 1
    out += '</ul>'
    return out
            
    