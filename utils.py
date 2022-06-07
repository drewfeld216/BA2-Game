def draw_db():
    from eralchemy import render_er
    # In order for this to work I had to make a small edit to eralchemy code, based on this issue: 
    # https://github.com/Alexis-benoist/eralchemy/issues/80
    render_er("sqlite:///game.db", "db.png")
    return