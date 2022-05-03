import os

from flask import Flask, render_template, request, redirect

from flaskr.db import Session, get_db

# create and configure the app
app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "super secret key"


# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass   

from . import auth
app.register_blueprint(auth.bp)

from . import game
app.register_blueprint(game.bp)

from . import user
app.register_blueprint(user.bp)

from . import data
app.register_blueprint(data.bp)

@app.route("/")
def blank():
    return redirect('/auth/login')

# student home/game page
@app.route('/home')
@auth.login_required
def index():
    return render_template('home.html')
    
    # admin home page
@app.route('/admin', methods=['GET', 'POST'])
@auth.admin_required
def admin():
    if request.method == 'POST':
        game_name = request.form['name']
        seed = request.form['seed']
        days = request.form['days']
        game.register_game(game_name, seed, days)
    return render_template('admin.html') 

@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()
