'''
This file handles the "static" aspects of the game simulation - specifically,
simulating those parts of the game that do *not* depend on the strategy chosen
for a specific user.

These are kept in a separate file because they can be run in bulk when the game
is generated - nothing needs to be done while the game is running

Note that
  - All functions prefixed with "add_" modify objects, and adds an element
    to those objects
  - Other functions return their results

Begin with the game_create() function, which simulates a whole game and calls most
other functions in the file
'''

import numpy as np

TOPIC_NAMES = ['Opinion', 'Politics', 'World Events', 'Business', 'Technology', 'Arts & Culture', 'Sports', 'Health', 'Home', 'Travel', 'Fashion', 'Food']
    
    
# ---------------------------------
# -  Section 1; base elements     -
# -  (Alphabetical by class name) -
# ---------------------------------

# Article
# -------

def article_wordcount(game):
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
    return np.maximum(0, np.minimum(1, game.generate_rv('normal', loc=0.5, scale=0.2)))

def article_author(topic):
    '''
    Given the topic of an article, this function will simulate the
    author that wrote it
    
    It uses the randomization engine in the game
    '''
    
    # Note that
    #                         P(Topic | Author) P(Author)
    #   P(Author | Topic) = -------------------------------
    #                                   P(Topic)
    #
    # With P(Topic) = sum over authors ( P(Topic | Author) P(Author) )
    
    # First, create a list called numerators that finds P(Topic | Author) P(Author)
    # for every author
    numerators = [[t_e.expertise for t_e in a.topic_expertises if t_e.topic==topic][0]
                                                * a.productivity for a in topic.game.authors]
    
    # Use that to find the probability each author wrote this article
    author_probs = [i/sum(numerators) for i in numerators]
    
    # Generate the author
    author = topic.game.generate_rv('choice', l=topic.game.authors, p=author_probs)
    
    return author
    
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
    
    for a, productivity in zip(game.authors, game.generate_rv('dirichlet',
                                                               alpha=alpha)):
        a.productivity = productivity

# Event
# -----

def events_per_day(game):
    '''
    This method will generate the number of events on any given
    day, using the randomization engine in a game
    
    This will be a Poisson distribution, calibrated to have a mean
    of 7 events a day    
    '''
    
    return game.generate_rv('poisson', lam=7)

def event_intensity(game):
    '''
    This method will generate the intensity of a specific
    event. It is calibrated to ensure the minimum intensity
    is 0.1, and this has highest probability. The probability
    then decreases until 1, where there is a small bump in
    probability because of the np.min
    '''
    return np.minimum(1, game.generate_rv('exponential', loc=0.1, scale=0.2))

def event_articles(event, day):
    '''
    Given a specific day, this function will simulate whether an article
    will be generated by this event on that day, and then find the topic
    of that article
    
    It will either return None if no article is generated, or else return
    the topic in question
    
    The game randomization engine will be used
    '''
    
    # Find the time effect (which will be 1 on day 0, and intensity
    # on day 4). For this to happen, the time effect needs to be
    #       exp( - days_since_event / alpha )
    # with
    #       alpha = -4/np.log(intensity)
    time_effect = np.exp(-(day - event.start)/ (-4/np.log(event.intensity)))
    
    # If the effect is smaller than 0.01, or if day is before the
    # event, no articles are produced
    if (time_effect <= 0.01) or (day < event.start):
        return None
    else:
        # Check whether an article will be published
        if event.game.generate_rv('uniform') > event.intensity*time_effect:
            return None
        else:
            topics = []
            relevances  = []
            for t_r in event.topic_relevances:
                topics.append(t_r.topic)
                relevances.append(t_r.relevance)
        
            return event.game.generate_rv('choice',
                                          l=topics,
                                          p=relevances)

# Game
# ----

def game_create(name, seed, n_days, n_days_p0, n_authors, n_users):
    

# User
# ----

def user_ip(game):
    return game.generate_rv('ipv4')

def user_agent(game):
    return game.generate_rv('agent')

def user_freq(game):
    return max(0, int(game.generate_rv('normal', loc=5, scale=5)))

def user_first_day(game):
    return int(game.generate_rv('uniform')*game.n_days)

def user_ad_sensitivity(game):
    return game.generate_rv('normal', loc=3, scale=1)

def user_age_and_income(game):
    # Data from https://www2.census.gov/programs-surveys/cps/tables/hinc-01/2021/hinc01_1.xlsx
    # Might not be the exact right table, but close enough
    
    cats = [{'age': '15 to 24', 'income': '0 to 5000'}, {'age': '15 to 24', 'income': '5000 to 9999'}, {'age': '15 to 24', 'income': '10000 to 14999'}, {'age': '15 to 24', 'income': '15000 to 19999'}, {'age': '15 to 24', 'income': '20000 to 24999'}, {'age': '15 to 24', 'income': '25000 to 29999'}, {'age': '15 to 24', 'income': '30000 to 34999'}, {'age': '15 to 24', 'income': '35000 to 39999'}, {'age': '15 to 24', 'income': '40000 to 44999'}, {'age': '15 to 24', 'income': '45000 to 49999'}, {'age': '15 to 24', 'income': '50000 to 54999'}, {'age': '15 to 24', 'income': '55000 to 59999'}, {'age': '15 to 24', 'income': '60000 to 64999'}, {'age': '15 to 24', 'income': '65000 to 69999'}, {'age': '15 to 24', 'income': '70000 to 74999'}, {'age': '15 to 24', 'income': '75000 to 79999'}, {'age': '15 to 24', 'income': '80000 to 84999'}, {'age': '15 to 24', 'income': '85000 to 89999'}, {'age': '15 to 24', 'income': '90000 to 94999'}, {'age': '15 to 24', 'income': '95000 to 99999'}, {'age': '15 to 24', 'income': '100000 to 104999'}, {'age': '15 to 24', 'income': '105000 to 109999'}, {'age': '15 to 24', 'income': '110000 to 114999'}, {'age': '15 to 24', 'income': '115000 to 119999'}, {'age': '15 to 24', 'income': '120000 to 124999'}, {'age': '15 to 24', 'income': '125000 to 129999'}, {'age': '15 to 24', 'income': '130000 to 134999'}, {'age': '15 to 24', 'income': '135000 to 139999'}, {'age': '15 to 24', 'income': '140000 to 144999'}, {'age': '15 to 24', 'income': '145000 to 149999'}, {'age': '15 to 24', 'income': '150000 to 154999'}, {'age': '15 to 24', 'income': '155000 to 159999'}, {'age': '15 to 24', 'income': '160000 to 164999'}, {'age': '15 to 24', 'income': '165000 to 169999'}, {'age': '15 to 24', 'income': '170000 to 174999'}, {'age': '15 to 24', 'income': '175000 to 179999'}, {'age': '15 to 24', 'income': '180000 to 184999'}, {'age': '15 to 24', 'income': '185000 to 189999'}, {'age': '15 to 24', 'income': '190000 to 194999'}, {'age': '15 to 24', 'income': '195000 to 199999'}, {'age': '15 to 24', 'income': '200000 and over'}, {'age': '25 to 34', 'income': '0 to 5000'}, {'age': '25 to 34', 'income': '5000 to 9999'}, {'age': '25 to 34', 'income': '10000 to 14999'}, {'age': '25 to 34', 'income': '15000 to 19999'}, {'age': '25 to 34', 'income': '20000 to 24999'}, {'age': '25 to 34', 'income': '25000 to 29999'}, {'age': '25 to 34', 'income': '30000 to 34999'}, {'age': '25 to 34', 'income': '35000 to 39999'}, {'age': '25 to 34', 'income': '40000 to 44999'}, {'age': '25 to 34', 'income': '45000 to 49999'}, {'age': '25 to 34', 'income': '50000 to 54999'}, {'age': '25 to 34', 'income': '55000 to 59999'}, {'age': '25 to 34', 'income': '60000 to 64999'}, {'age': '25 to 34', 'income': '65000 to 69999'}, {'age': '25 to 34', 'income': '70000 to 74999'}, {'age': '25 to 34', 'income': '75000 to 79999'}, {'age': '25 to 34', 'income': '80000 to 84999'}, {'age': '25 to 34', 'income': '85000 to 89999'}, {'age': '25 to 34', 'income': '90000 to 94999'}, {'age': '25 to 34', 'income': '95000 to 99999'}, {'age': '25 to 34', 'income': '100000 to 104999'}, {'age': '25 to 34', 'income': '105000 to 109999'}, {'age': '25 to 34', 'income': '110000 to 114999'}, {'age': '25 to 34', 'income': '115000 to 119999'}, {'age': '25 to 34', 'income': '120000 to 124999'}, {'age': '25 to 34', 'income': '125000 to 129999'}, {'age': '25 to 34', 'income': '130000 to 134999'}, {'age': '25 to 34', 'income': '135000 to 139999'}, {'age': '25 to 34', 'income': '140000 to 144999'}, {'age': '25 to 34', 'income': '145000 to 149999'}, {'age': '25 to 34', 'income': '150000 to 154999'}, {'age': '25 to 34', 'income': '155000 to 159999'}, {'age': '25 to 34', 'income': '160000 to 164999'}, {'age': '25 to 34', 'income': '165000 to 169999'}, {'age': '25 to 34', 'income': '170000 to 174999'}, {'age': '25 to 34', 'income': '175000 to 179999'}, {'age': '25 to 34', 'income': '180000 to 184999'}, {'age': '25 to 34', 'income': '185000 to 189999'}, {'age': '25 to 34', 'income': '190000 to 194999'}, {'age': '25 to 34', 'income': '195000 to 199999'}, {'age': '25 to 34', 'income': '200000 and over'}, {'age': '35 to 44', 'income': '0 to 5000'}, {'age': '35 to 44', 'income': '5000 to 9999'}, {'age': '35 to 44', 'income': '10000 to 14999'}, {'age': '35 to 44', 'income': '15000 to 19999'}, {'age': '35 to 44', 'income': '20000 to 24999'}, {'age': '35 to 44', 'income': '25000 to 29999'}, {'age': '35 to 44', 'income': '30000 to 34999'}, {'age': '35 to 44', 'income': '35000 to 39999'}, {'age': '35 to 44', 'income': '40000 to 44999'}, {'age': '35 to 44', 'income': '45000 to 49999'}, {'age': '35 to 44', 'income': '50000 to 54999'}, {'age': '35 to 44', 'income': '55000 to 59999'}, {'age': '35 to 44', 'income': '60000 to 64999'}, {'age': '35 to 44', 'income': '65000 to 69999'}, {'age': '35 to 44', 'income': '70000 to 74999'}, {'age': '35 to 44', 'income': '75000 to 79999'}, {'age': '35 to 44', 'income': '80000 to 84999'}, {'age': '35 to 44', 'income': '85000 to 89999'}, {'age': '35 to 44', 'income': '90000 to 94999'}, {'age': '35 to 44', 'income': '95000 to 99999'}, {'age': '35 to 44', 'income': '100000 to 104999'}, {'age': '35 to 44', 'income': '105000 to 109999'}, {'age': '35 to 44', 'income': '110000 to 114999'}, {'age': '35 to 44', 'income': '115000 to 119999'}, {'age': '35 to 44', 'income': '120000 to 124999'}, {'age': '35 to 44', 'income': '125000 to 129999'}, {'age': '35 to 44', 'income': '130000 to 134999'}, {'age': '35 to 44', 'income': '135000 to 139999'}, {'age': '35 to 44', 'income': '140000 to 144999'}, {'age': '35 to 44', 'income': '145000 to 149999'}, {'age': '35 to 44', 'income': '150000 to 154999'}, {'age': '35 to 44', 'income': '155000 to 159999'}, {'age': '35 to 44', 'income': '160000 to 164999'}, {'age': '35 to 44', 'income': '165000 to 169999'}, {'age': '35 to 44', 'income': '170000 to 174999'}, {'age': '35 to 44', 'income': '175000 to 179999'}, {'age': '35 to 44', 'income': '180000 to 184999'}, {'age': '35 to 44', 'income': '185000 to 189999'}, {'age': '35 to 44', 'income': '190000 to 194999'}, {'age': '35 to 44', 'income': '195000 to 199999'}, {'age': '35 to 44', 'income': '200000 and over'}, {'age': '45 to 54', 'income': '0 to 5000'}, {'age': '45 to 54', 'income': '5000 to 9999'}, {'age': '45 to 54', 'income': '10000 to 14999'}, {'age': '45 to 54', 'income': '15000 to 19999'}, {'age': '45 to 54', 'income': '20000 to 24999'}, {'age': '45 to 54', 'income': '25000 to 29999'}, {'age': '45 to 54', 'income': '30000 to 34999'}, {'age': '45 to 54', 'income': '35000 to 39999'}, {'age': '45 to 54', 'income': '40000 to 44999'}, {'age': '45 to 54', 'income': '45000 to 49999'}, {'age': '45 to 54', 'income': '50000 to 54999'}, {'age': '45 to 54', 'income': '55000 to 59999'}, {'age': '45 to 54', 'income': '60000 to 64999'}, {'age': '45 to 54', 'income': '65000 to 69999'}, {'age': '45 to 54', 'income': '70000 to 74999'}, {'age': '45 to 54', 'income': '75000 to 79999'}, {'age': '45 to 54', 'income': '80000 to 84999'}, {'age': '45 to 54', 'income': '85000 to 89999'}, {'age': '45 to 54', 'income': '90000 to 94999'}, {'age': '45 to 54', 'income': '95000 to 99999'}, {'age': '45 to 54', 'income': '100000 to 104999'}, {'age': '45 to 54', 'income': '105000 to 109999'}, {'age': '45 to 54', 'income': '110000 to 114999'}, {'age': '45 to 54', 'income': '115000 to 119999'}, {'age': '45 to 54', 'income': '120000 to 124999'}, {'age': '45 to 54', 'income': '125000 to 129999'}, {'age': '45 to 54', 'income': '130000 to 134999'}, {'age': '45 to 54', 'income': '135000 to 139999'}, {'age': '45 to 54', 'income': '140000 to 144999'}, {'age': '45 to 54', 'income': '145000 to 149999'}, {'age': '45 to 54', 'income': '150000 to 154999'}, {'age': '45 to 54', 'income': '155000 to 159999'}, {'age': '45 to 54', 'income': '160000 to 164999'}, {'age': '45 to 54', 'income': '165000 to 169999'}, {'age': '45 to 54', 'income': '170000 to 174999'}, {'age': '45 to 54', 'income': '175000 to 179999'}, {'age': '45 to 54', 'income': '180000 to 184999'}, {'age': '45 to 54', 'income': '185000 to 189999'}, {'age': '45 to 54', 'income': '190000 to 194999'}, {'age': '45 to 54', 'income': '195000 to 199999'}, {'age': '45 to 54', 'income': '200000 and over'}, {'age': '55 to 64', 'income': '0 to 5000'}, {'age': '55 to 64', 'income': '5000 to 9999'}, {'age': '55 to 64', 'income': '10000 to 14999'}, {'age': '55 to 64', 'income': '15000 to 19999'}, {'age': '55 to 64', 'income': '20000 to 24999'}, {'age': '55 to 64', 'income': '25000 to 29999'}, {'age': '55 to 64', 'income': '30000 to 34999'}, {'age': '55 to 64', 'income': '35000 to 39999'}, {'age': '55 to 64', 'income': '40000 to 44999'}, {'age': '55 to 64', 'income': '45000 to 49999'}, {'age': '55 to 64', 'income': '50000 to 54999'}, {'age': '55 to 64', 'income': '55000 to 59999'}, {'age': '55 to 64', 'income': '60000 to 64999'}, {'age': '55 to 64', 'income': '65000 to 69999'}, {'age': '55 to 64', 'income': '70000 to 74999'}, {'age': '55 to 64', 'income': '75000 to 79999'}, {'age': '55 to 64', 'income': '80000 to 84999'}, {'age': '55 to 64', 'income': '85000 to 89999'}, {'age': '55 to 64', 'income': '90000 to 94999'}, {'age': '55 to 64', 'income': '95000 to 99999'}, {'age': '55 to 64', 'income': '100000 to 104999'}, {'age': '55 to 64', 'income': '105000 to 109999'}, {'age': '55 to 64', 'income': '110000 to 114999'}, {'age': '55 to 64', 'income': '115000 to 119999'}, {'age': '55 to 64', 'income': '120000 to 124999'}, {'age': '55 to 64', 'income': '125000 to 129999'}, {'age': '55 to 64', 'income': '130000 to 134999'}, {'age': '55 to 64', 'income': '135000 to 139999'}, {'age': '55 to 64', 'income': '140000 to 144999'}, {'age': '55 to 64', 'income': '145000 to 149999'}, {'age': '55 to 64', 'income': '150000 to 154999'}, {'age': '55 to 64', 'income': '155000 to 159999'}, {'age': '55 to 64', 'income': '160000 to 164999'}, {'age': '55 to 64', 'income': '165000 to 169999'}, {'age': '55 to 64', 'income': '170000 to 174999'}, {'age': '55 to 64', 'income': '175000 to 179999'}, {'age': '55 to 64', 'income': '180000 to 184999'}, {'age': '55 to 64', 'income': '185000 to 189999'}, {'age': '55 to 64', 'income': '190000 to 194999'}, {'age': '55 to 64', 'income': '195000 to 199999'}, {'age': '55 to 64', 'income': '200000 and over'}, {'age': '65 to 74', 'income': '0 to 5000'}, {'age': '65 to 74', 'income': '5000 to 9999'}, {'age': '65 to 74', 'income': '10000 to 14999'}, {'age': '65 to 74', 'income': '15000 to 19999'}, {'age': '65 to 74', 'income': '20000 to 24999'}, {'age': '65 to 74', 'income': '25000 to 29999'}, {'age': '65 to 74', 'income': '30000 to 34999'}, {'age': '65 to 74', 'income': '35000 to 39999'}, {'age': '65 to 74', 'income': '40000 to 44999'}, {'age': '65 to 74', 'income': '45000 to 49999'}, {'age': '65 to 74', 'income': '50000 to 54999'}, {'age': '65 to 74', 'income': '55000 to 59999'}, {'age': '65 to 74', 'income': '60000 to 64999'}, {'age': '65 to 74', 'income': '65000 to 69999'}, {'age': '65 to 74', 'income': '70000 to 74999'}, {'age': '65 to 74', 'income': '75000 to 79999'}, {'age': '65 to 74', 'income': '80000 to 84999'}, {'age': '65 to 74', 'income': '85000 to 89999'}, {'age': '65 to 74', 'income': '90000 to 94999'}, {'age': '65 to 74', 'income': '95000 to 99999'}, {'age': '65 to 74', 'income': '100000 to 104999'}, {'age': '65 to 74', 'income': '105000 to 109999'}, {'age': '65 to 74', 'income': '110000 to 114999'}, {'age': '65 to 74', 'income': '115000 to 119999'}, {'age': '65 to 74', 'income': '120000 to 124999'}, {'age': '65 to 74', 'income': '125000 to 129999'}, {'age': '65 to 74', 'income': '130000 to 134999'}, {'age': '65 to 74', 'income': '135000 to 139999'}, {'age': '65 to 74', 'income': '140000 to 144999'}, {'age': '65 to 74', 'income': '145000 to 149999'}, {'age': '65 to 74', 'income': '150000 to 154999'}, {'age': '65 to 74', 'income': '155000 to 159999'}, {'age': '65 to 74', 'income': '160000 to 164999'}, {'age': '65 to 74', 'income': '165000 to 169999'}, {'age': '65 to 74', 'income': '170000 to 174999'}, {'age': '65 to 74', 'income': '175000 to 179999'}, {'age': '65 to 74', 'income': '180000 to 184999'}, {'age': '65 to 74', 'income': '185000 to 189999'}, {'age': '65 to 74', 'income': '190000 to 194999'}, {'age': '65 to 74', 'income': '195000 to 199999'}, {'age': '65 to 74', 'income': '200000 and over'}, {'age': '75 and over', 'income': '0 to 5000'}, {'age': '75 and over', 'income': '5000 to 9999'}, {'age': '75 and over', 'income': '10000 to 14999'}, {'age': '75 and over', 'income': '15000 to 19999'}, {'age': '75 and over', 'income': '20000 to 24999'}, {'age': '75 and over', 'income': '25000 to 29999'}, {'age': '75 and over', 'income': '30000 to 34999'}, {'age': '75 and over', 'income': '35000 to 39999'}, {'age': '75 and over', 'income': '40000 to 44999'}, {'age': '75 and over', 'income': '45000 to 49999'}, {'age': '75 and over', 'income': '50000 to 54999'}, {'age': '75 and over', 'income': '55000 to 59999'}, {'age': '75 and over', 'income': '60000 to 64999'}, {'age': '75 and over', 'income': '65000 to 69999'}, {'age': '75 and over', 'income': '70000 to 74999'}, {'age': '75 and over', 'income': '75000 to 79999'}, {'age': '75 and over', 'income': '80000 to 84999'}, {'age': '75 and over', 'income': '85000 to 89999'}, {'age': '75 and over', 'income': '90000 to 94999'}, {'age': '75 and over', 'income': '95000 to 99999'}, {'age': '75 and over', 'income': '100000 to 104999'}, {'age': '75 and over', 'income': '105000 to 109999'}, {'age': '75 and over', 'income': '110000 to 114999'}, {'age': '75 and over', 'income': '115000 to 119999'}, {'age': '75 and over', 'income': '120000 to 124999'}, {'age': '75 and over', 'income': '125000 to 129999'}, {'age': '75 and over', 'income': '130000 to 134999'}, {'age': '75 and over', 'income': '135000 to 139999'}, {'age': '75 and over', 'income': '140000 to 144999'}, {'age': '75 and over', 'income': '145000 to 149999'}, {'age': '75 and over', 'income': '150000 to 154999'}, {'age': '75 and over', 'income': '155000 to 159999'}, {'age': '75 and over', 'income': '160000 to 164999'}, {'age': '75 and over', 'income': '165000 to 169999'}, {'age': '75 and over', 'income': '170000 to 174999'}, {'age': '75 and over', 'income': '175000 to 179999'}, {'age': '75 and over', 'income': '180000 to 184999'}, {'age': '75 and over', 'income': '185000 to 189999'}, {'age': '75 and over', 'income': '190000 to 194999'}, {'age': '75 and over', 'income': '195000 to 199999'}, {'age': '75 and over', 'income': '200000 and over'}]
    freqs = [348, 183, 208, 284, 287, 321, 358, 327, 307, 276, 299, 270, 203, 192, 185, 149, 164, 93, 124, 135, 88, 55, 82, 48, 59, 43, 18, 26, 31, 22, 28, 28, 49, 14, 12, 17, 18, 5, 6, 7, 117, 619, 368, 441, 523, 755, 690, 794, 874, 883, 806, 926, 787, 803, 773, 792, 751, 713, 587, 604, 455, 612, 491, 409, 297, 391, 310, 323, 257, 236, 235, 233, 217, 166, 178, 186, 163, 157, 108, 128, 96, 1516, 598, 376, 471, 472, 572, 597, 763, 754, 746, 689, 827, 625, 769, 607, 716, 723, 652, 529, 583, 564, 609, 476, 507, 394, 530, 351, 359, 334, 338, 302, 371, 243, 279, 170, 252, 223, 233, 170, 169, 123, 3042, 581, 378, 601, 572, 630, 544, 604, 653, 653, 605, 712, 595, 675, 676, 682, 611, 534, 480, 536, 473, 609, 429, 472, 375, 392, 376, 358, 341, 284, 274, 353, 287, 310, 241, 220, 201, 211, 201, 166, 196, 3571, 807, 699, 1037, 973, 906, 823, 902, 861, 852, 683, 869, 761, 750, 676, 654, 605, 572, 555, 602, 518, 582, 427, 540, 363, 404, 351, 335, 321, 296, 271, 355, 251, 216, 189, 252, 218, 203, 146, 224, 154, 3134, 643, 465, 1086, 1249, 1189, 1091, 1014, 944, 932, 951, 834, 711, 663, 554, 615, 570, 521, 410, 395, 342, 406, 364, 297, 257, 266, 241, 203, 233, 214, 203, 165, 125, 167, 147, 150, 104, 96, 81, 104, 77, 1422, 614, 457, 1265, 1596, 1269, 1120, 893, 873, 728, 675, 595, 553, 401, 340, 326, 272, 335, 218, 241, 191, 215, 153, 162, 116, 99, 98, 94, 116, 79, 64, 71, 69, 64, 55, 38, 53, 23, 44, 51, 42, 517]
    
    return generate_rv('choice', l=cats, p=freqs)
    
def user_media_consumption(game):
    # TODO
    return 0
   
def user_internet_usage_index(game):
    # TODO
    return 0
    
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
    alpha = np.ones(len(author.topic_expertises))*0.3
    
    for t_e, expertise in zip(author.topic_expertises, game.generate_rv('dirichlet',
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
    
    for a, productivity in zip(game.authors, game.generate_rv('dirichlet',
                                                               alpha=alpha)):
        a.productivity = productivity

# EventTopic
# ----------

def add_event_relevances(author, game):
    '''
    This function generates a dictionary of topic relevances
    for an event, one for each topic. The list of topic is
    pulled from the game, and the game randomization seeds is
    used
    '''
    
    # Create an alpha parameter that ensures more relevance
    # will be concentrated on a few topics
    alpha = np.ones(len(game.topics))*0.3
    
    for t_r, relevance in zip(author.topic_relevances, game.generate_rv('dirichlet',
                                                                         alpha=alpha)):
        t_r.relevance = relevance

# UserTopic
# ---------

#def add_user_interests(

# UserAuthor
# ----------

#def add_user_affinities