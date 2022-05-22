
# ---------------------------------
# -  Section 1; base elements     -
# -  (Alphabetical by class name) -
# ---------------------------------

# Article
# -------

def article_length(game):
    '''
    Generates the length of an article using the randomization
    engine in a game
    '''
    return int(game.generate_rv('uniform', low=300, high=2000))
    
def article_vocab(game):
    '''
    Generates the vocabulary complexity of an article using
    the randomization engine in the game
    '''
    return np.max(0, np.min(1, game.generate_rv('normal', loc=0.5, scale=0.2)))

# Author
# ------

def author_name(game):
    '''
    Generates an author name, using the randomization engine in the
    game
    '''
    return game.generate_rv('name')

def author_quality(game):
    '''
    Generates the quality of an author using the randomization
    engine in a game
    '''
    return game.generate_rv('uniform')*10

def add_author_productivities(game):
    '''
    Looks at the list of authors in a game, and adds productivities to
    them
    '''
    
    # Create an alpha parameter that ensures the productivity will
    # be roughly evenly split between authors
    alpha = np.ones(len(game.authors))*1
    
    for a, productivity in zip(game.authors, game.generate_rvs('dirichlet',
                                                               alpha=alpha)):
        a.productivity = productivity
    
# Event
# -----

def events_per_day(game):
    '''
    This method will generate the number of events on any
    given day, using the randomization engine in a game
    '''
    return game.generate_rv('choice',
                            l=[0, 1, 2, 3],
                            p=[0.3, 0.3, 0.2, 0.2])

def event_intensity(game):
    '''
    This method will generate the intensity of a specific
    event. It is calibrated to ensure the minimum intensity
    is 1, and this has highest probability. The probability
    then decreases until 10, where there is a small bump in
    probability because of the np.min
    '''
    return np.min(10, game.generate_rv('exponential', loc=1, scale=2))
    
# --------------------------------------
# -  Section 2; many-to-many tables    -
# -  (Alphabetical by class name)      -
# --------------------------------------

# AuthorTopic
# -----------

def add_author_expertises(author, game):
    '''
    Looks at a specific author, and adds expertises for each topic
    for that author. Uses the game randomization engine
    '''
    
    # Create an alpha parameter that ensures expertise will be highly
    # concentrated on some topics
    alpha = np.ones(len(author.topic_expertises))*0.5
    
    for t_e, expertise in zip(author.topic_expertises, game.generate_rvs('dirichlet',
                                                                         alpha=alpha)):
        t_e.expertise = expertise

def add_author_productivities(game):
    '''
    Looks at the list of authors in a game, and adds productivities to
    them
    '''
    
    # Create an alpha parameter that ensures the productivity will
    # be roughly evenly split between authors
    alpha = np.ones(len(game.authors))*1
    
    for a, productivity in zip(game.authors, game.generate_rvs('dirichlet',
                                                               alpha=alpha)):
        a.productivity = productivity

# EventTopic
# ----------

def event_topic_relevances(game):
    '''
    This function generates a dictionary of topic relevances
    for an event, one for each topic. The list of topic is
    pulled from the game, and the game randomization seed is
    used
    '''
    
    # Create an alpha parameter that ensures more relevance
    # will be concentrated on a few topics
    alpha = np.ones(len(game.topics))*0.2
    
    return {t:j for t, j in zip(game.topics, game.generate_rv('dirichlet',
                                                              alpha=alpha))}

