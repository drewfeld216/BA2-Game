import click
from flask import current_app, g
from flask.cli import with_appcontext

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, registry

from werkzeug.security import generate_password_hash


engine = create_engine('sqlite:///game.db', convert_unicode=True)
Session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
mapper_registry = registry()
Base = mapper_registry.generate_base()

def create_db():
    import flaskr.models as mdl
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    drew_admin = mdl.Player(email='drewadmin', password=generate_password_hash('pass'), type='admin', status='confirmed')
    Session.add(drew_admin)
    drew_student = mdl.Player(email='drewstudent', password=generate_password_hash('pass'), type='student', status='confirmed')
    Session.add(drew_student)
    Session.commit() 
    
@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    create_db()
    click.echo('Initialized the database.')
    

def get_db():
    from os.path import exists

    if exists('./game.db'):
        return Session
    else:
        create_db()
        return Session

def close_db(e=None):
    #db = 
    return
        
        
def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)