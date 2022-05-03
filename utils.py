from eralchemy import render_er

def draw_db():
    render_er("sqlite:///game.db", "db.png")
    return