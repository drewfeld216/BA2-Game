import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from flaskr.auth import login_required, admin_required

bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('pending', methods=('GET', 'POST'))
@admin_required
def pendingBlock():
    admin = g.user['id']
    return userTableBlock(admin_id = admin)

@bp.route('confirmed', methods=('GET', 'POST'))
@admin_required
def confirmedBlock():
    game = request.args.get('game')
    return userTableBlock(game_id = game)
    
@bp.route('approve', methods=('GET', 'POST'))
@admin_required
def approveUser():
    user_id = request.args.get('user')
    db = get_db()
    
    db.execute(
        'UPDATE user SET status = ? WHERE id = ?', ('confirmed', user_id,)    
    )
    db.commit()
    return redirect('/admin')

def userTableBlock(**kwargs):
    pending = 0
    confirmed = 0
    if 'admin_id' in kwargs:
        pending = 1
        admin_id = kwargs['admin_id']
    elif 'game_id' in kwargs:
        confirmed = 1
        game_id = kwargs['game_id']
    else:
        return
        
    out = '''<div class="container">
                <div class="row">
                    <div class="col">
                        <div class="panel panel-default">
                            <div class="panel-heading">
                            </div>
                            <div class="panel-body">'''             
    out += '\n'
    try:
        if pending == 1:
            table = getPendingTable(admin_id)
        elif confirmed == 1:
            table = getConfirmedTable(game_id)
        
        if table == 0:
            return ""
        else:
            out += table

    except:
        return ""
    
    out += '''              </div>
                        </div>
                    </div>
                </div>
            </div>'''
    return out

def getPendingTable(admin_id):
    db = get_db()
    try:
        games = db.execute(
            'SELECT * FROM game WHERE admin = ?', (admin_id,)
        ).fetchall()
        game_info = {int(game['id']): game['name'] for game in games}
        
        users = []
        for game_id in game_info.keys():
            new_users = db.execute(
                'SELECT * FROM user WHERE status = ? AND game_id = ?', ('pending', game_id,)
            ).fetchall()
            users.extend(new_users)
    except:
        return
        
    if len(users) == 0:
        return 0
    
    out = '<table class="table table-striped">' + '\n'
    out += '''    <thead>
                      <tr>
                          <th scope="col">Game ID</th>
                          <th scope="col">Team Name</th>
                          <th scope="col">Members</th>
                          <th scope="col"></th>
                      </tr>
                  </thead>''' + '\n'
    out += '    <tbody>' + '\n'
    for user in users:
        out += '        <tr>' + '\n'
        out += '            <th scope="row">' + str(user['game_id']) + '</th>' + '\n'
        out += '            <th>' + user['name'] + '</th>' + '\n'
        out += '            <th>' + user['members'] + '</th>' + '\n'
        out += '            <th><a style="color: white" href="user/approve?user=' + str(user['id']) + '"><button type="button" class="btn btn-success approve-btn">Confirm</button></a></th>' + '\n'
        out += '        </tr>' + '\n'
    out += '    </tbody' + '\n'
    out += '</table>'
    return out
    
def getConfirmedTable(game_id):
    db = get_db()
    try:
        users = db.execute(
            'SELECT * FROM user WHERE status = ? AND game_id = ?', ('confirmed', game_id,)
        ).fetchall()
    except:
        return
        
    if len(users) == 0:
        return 0
    
    out = '<table class="table table-striped">' + '\n'
    out += '''    <thead>
                      <tr>
                          <th scope="col">Game ID</th>
                          <th scope="col">Team Name</th>
                          <th scope="col">Members</th>
                      </tr>
                  </thead>''' + '\n'
    out += '    <tbody>' + '\n'
    for user in users:
        out += '        <tr>' + '\n'
        out += '            <th scope="row">' + str(user['game_id']) + '</th>' + '\n'
        out += '            <th>' + user['name'] + '</th>' + '\n'
        out += '            <th>' + user['members'] + '</th>' + '\n'
        out += '        </tr>' + '\n'
    out += '    </tbody' + '\n'
    out += '</table>'
    return out



