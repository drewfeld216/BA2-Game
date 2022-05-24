import rand_utils

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm

import pandas as pd
import numpy as np

################

import itertools

from metrics import log_metric

engine          = sa.create_engine('sqlite:///game.db')
Session         = sa_orm.sessionmaker(engine)

mapper_registry = sa_orm.registry()
Base            = mapper_registry.generate_base()

def run_sql(s):
    with engine.connect() as con:
        return pd.DataFrame(con.execute(s).fetchall())

def create_db():
    mapper_registry.metadata.drop_all(engine)
    mapper_registry.metadata.create_all(engine)

# not an ORM wrapper
class BaseStrategy:
    cost = 9
    ads = 3
    free_pvs = 12

# ---------------------------------
# -  Section 1; base elements     -
# -  (Alphabetical by class name) -
# ---------------------------------

class Article(Base):
    '''
    A specific article, associated with a game
      - day       : the day on which the article was published
                       --> generated via events in simulate_static.game
      - wordcount : the number of words in the article
                       --> generated in simulate_static.article_wordcount
      - vocab     : a score between 0 and 1 indicating the complexity
                    of the vocabulary in this article
                       --> generated in simulate_static.article_vocab
      - topic     : the topic of the article
                       --> generated via events in simulate_static.game
      - author    : the author of the article
                       --> generated based on the topic in
                           simulate_static.article_author
    '''
    
    __tablename__ = 'article'
    
    id        = sa.Column(sa.Integer, primary_key=True)
    game_id   = sa.Column(sa.ForeignKey('game.id'))
    topic_id  = sa.Column(sa.ForeignKey('topic.id'))
    author_id = sa.Column(sa.ForeignKey('author.id'))
    
    day       = sa.Column(sa.Integer)
    wordcount = sa.Column(sa.Integer)
    vocab     = sa.Column(sa.Integer)
    
    game      = sa_orm.relationship('Game', back_populates='articles')
    topic     = sa_orm.relationship('Topic')
    author    = sa_orm.relationship('Author')
    
class Author(Base):
    '''
    A specific author, associated with a game
      - name             : the name of the author
                               --> generated in simulate_static.author_name
      - quality          : a number between 0 and 10 indicating the quality of
                           the author
                               --> generated in simulate_static.author_quality
      - productivity     : the productivity of the author (i.e., how often
                           they write articles). These are expressed as the
                           probability THIS author will write an article if
                           *any* author will write an article; these will sum
                           to 1 over all the authors
                               --> generated in simulate_static.add_author_productivities
      - topic_expertises : indicates the fact that a given author might have
                           an expertise in a specific topic. Each author and topic
                           will have a row in AuthorTopic; see there for details
    '''
    
    __tablename__ = 'author'
    
    id                = sa.Column(sa.Integer,  primary_key=True)
    game_id           = sa.Column(sa.ForeignKey('game.id'))
    
    name              = sa.Column(sa.String(50))
    quality           = sa.Column(sa.Integer)
    productivity      = sa.Column(sa.Integer)
    
    game              = sa_orm.relationship('Game', back_populates='authors')
    topic_expertises  = sa_orm.relationship('AuthorTopic', back_populates='author')
    
    def topic_expertise(self, topic):
        '''
        Returns the topic_expertise object for a specific topic
        object
        '''
        
        out = [t_e for t_e in self.topic_expertises if t_e.topic == topic]
        
        assert len(out) == 1
        
        return out[0]
        

class Event(Base):
    '''
    A specific event, associated with a game
      - start            : the day on which the event begins
                                --> Generated in simulate_static.game_static
      - intensity        : the intensity of the event, a number between 0.1 and 1
                           that indicates the probability the event will lead to an
                           article on the day the event happens. The event then continues
                           to have an exponentially decreasing influence in the subsequent
                           days; the higher the intensity, the longer-lasting the event;
                           the exponential decay is calibrated so that the probability of
                           an article is intensity^2 on the 4th day
                           
                           For example, if intensity=0.8, the probability the event will
                           lead to an article on day 0 will be 0.8. Four days later, the
                           probability will be 0.8*0.8
                                --> Generated in simulate_static.event_intensity
      - topic_relevances : indicates the fact a given event might lead to articles of
                           certain topics with different probabilities. Each event and
                           topic will have a row in EventTopic; see there for details
    '''

    __tablename__ = 'event'
    
    id                = sa.Column(sa.Integer, primary_key=True)
    game_id           = sa.Column(sa.ForeignKey('game.id'))
    
    start             = sa.Column(sa.Integer)
    intensity         = sa.Column(sa.Integer)
    
    game              = sa_orm.relationship('Game', back_populates='events')
    topic_relevances  = sa_orm.relationship('EventTopic',back_populates='event')
        
class Game(Base, rand_utils.Rand_utils_mixin):
    '''
    This class describes a specific game
      - The variables starting with n_ are simulation parameters
      - See the documentation in rand_utils for an explanation of
        random_state
    '''
    
    __tablename__ = 'game'
    
    id           = sa.Column(sa.Integer, primary_key=True)
    
    seed         = sa.Column(sa.Integer, nullable=False)
    name         = sa.Column(sa.String(50))
    
    # Simulation parameters
    n_days       = sa.Column(sa.Integer, nullable=False)
    n_days_p0    = sa.Column(sa.Integer, nullable=False)
    n_authors    = sa.Column(sa.Integer, nullable=False)
    n_users      = sa.Column(sa.Integer, nullable=False)
    
    random_state = sa.Column(sa.String(20000), default='')
    
    teams        = sa_orm.relationship('Team', back_populates='game')
    topics       = sa_orm.relationship('Topic', back_populates='game')
    authors      = sa_orm.relationship('Author', back_populates='game')
    events       = sa_orm.relationship('Event', back_populates='game')
    articles     = sa_orm.relationship('Article', back_populates='game')
    users        = sa_orm.relationship('User', back_populates='game')

class Pageview(Base):
    '''
    This class represents a pageview a specific user saw in a specific
    game
    '''
    
    __tablename__ = 'pageview'
    
    id          = sa.Column(sa.Integer, primary_key=True)
    user_id     = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    article_id  = sa.Column(sa.Integer, sa.ForeignKey('article.id'))
    team_id     = sa.Column(sa.Integer, sa.ForeignKey('team.id'))
    
    day         = sa.Column(sa.Integer)
    duration    = sa.Column(sa.Integer)
    ads_seen    = sa.Column(sa.Integer)
    saw_paywall = sa.Column(sa.Boolean)
    converted   = sa.Column(sa.Boolean)
    
    user        = sa_orm.relationship('User', back_populates='pageviews')
    article     = sa_orm.relationship('Article')
    team        = sa_orm.relationship('Team')

class Player(Base):
    '''
    This class represents a single player, who might belong to one
    or more teams (the many-to-many relationship is mediated through
    PlayerTeam)
    '''
    
    __tablename__ = 'player'
    
    id              = sa.Column(sa.Integer, primary_key=True)
    email           = sa.Column(sa.String(50), nullable=False)
    hashed_password = sa.Column(sa.String(50), nullable=False)
    
    teams = sa_orm.relationship('Team', secondary='player_team', back_populates='players')

class Strategy(Base):
    '''
    This class describes a strategy
    
    TODO
    '''

    __tablename__ = 'strategy'
    
    id             = sa.Column(sa.Integer, primary_key=True)
    team_id        = sa.Column(sa.Integer, sa.ForeignKey('team.id'))
    
    cost           = sa.Column(sa.Float)
    ads            = sa.Column(sa.Integer)
    free_pvs       = sa.Column(sa.Integer)
    
    team           = sa_orm.relationship('Team')
    users_assigned = sa_orm.relationship('UserStrategy', back_populates='strategy')

class Team(Base, rand_utils.Rand_utils_mixin):
    '''
    This class describes a specific team, in a specific game
    
    Each team will have its own randomization engine, to ensure that
    one team's actions do not in any  way impact the random path that
    will be observed by another team.
    
    See rand_utils for an explanation of this works
    '''

    __tablename__ = 'team'
    
    id           = sa.Column(sa.Integer, primary_key=True)
    game_id      = sa.Column(sa.ForeignKey('game.id'))
    
    seed         = sa.Column(sa.Integer, nullable=False)
    name         = sa.Column(sa.String(50))
    
    random_state = sa.Column(sa.String(20000), default='')
    
    game         = sa_orm.relationship('Game', back_populates='teams')
    strategies   = sa_orm.relationship('Strategy', back_populates='team')
    players      = sa_orm.relationship('Player', secondary='player_team', back_populates='teams')

class Topic(Base):
    '''
    A specific topic, associated with a game
    '''
    
    __tablename__ = 'topic'
    
    id      = sa.Column(sa.Integer, primary_key=True)
    game_id = sa.Column(sa.ForeignKey('game.id'))
    
    name    = sa.Column(sa.String(50))
    
    game    = sa_orm.relationship('Game', back_populates='topics')

class User(Base):
    '''
    This class represents a single user, associated with one specific
    game. Most data generated in simulate_static
    '''
    
    __tablename__  = 'user'
    
    id             = sa.Column(sa.Integer, primary_key=True)
    game_id        = sa.Column(sa.ForeignKey('game.id'))
    
    # Basic attributes
    ip             = sa.Column(sa.String(20))
    agent          = sa.Column(sa.String(100))
    freq           = sa.Column(sa.Integer)
    first_day      = sa.Column(sa.Integer)
    ad_sensitivity = sa.Column(sa.Float)
    ad_blocked     = sa.Column(sa.Boolean)

    # Attributes that need to be purhcased
    age                  = sa.Column(sa.String(10))
    household_income     = sa.Column(sa.String(10))
    media_consumption    = sa.Column(sa.Integer)
    internet_usage_index = sa.Column(sa.Integer)

    game              = sa_orm.relationship('Game', back_populates='users')
    topic_interests   = sa_orm.relationship('UserTopic', back_populates='user')
    author_affinities = sa_orm.relationship('UserAuthor', back_populates='user')
    pageviews         = sa_orm.relationship('Pageview', back_populates='user', lazy='dynamic')
    strategies        = sa_orm.relationship('UserStrategy', back_populates='user')

# --------------------------------------
# -  Section 2; many-to-many tables    -
# -  (Alphabetical by class name)      -
# --------------------------------------

class AuthorTopic(Base):
    '''
    Many-to-many connection between author and topic
      - expertise : the author's expertise for that topic
    '''
    
    __tablename__ = 'author_topic'
    
    author_id = sa.Column(sa.ForeignKey('author.id'), primary_key=True)
    topic_id  = sa.Column(sa.ForeignKey('topic.id'), primary_key=True)
    
    expertise = sa.Column(sa.Float)
    
    author    = sa_orm.relationship('Author', back_populates='topic_expertises')
    topic     = sa_orm.relationship('Topic')
    
class EventTopic(Base):
    '''
    Many-to-many connection between event and topic
      - relevance : how relevant this topic is to that event.
                    For each event, relevances sum to 1 for all
                    topics
    '''
    
    __tablename__ = 'event_topic'
    
    event_id  = sa.Column(sa.ForeignKey('event.id'), primary_key=True)
    topic_id  = sa.Column(sa.ForeignKey('topic.id'), primary_key=True)
    
    relevance = sa.Column(sa.Float)
    
    event     = sa_orm.relationship('Event', back_populates='topic_relevances')
    topic     = sa_orm.relationship('Topic')

class PlayerTeam(Base):
    '''
    This class denotes the fact a player should have access to
    a specific team. It is a many-to-many association table
    '''
    
    __tablename__ = 'player_team'
    
    player_id = sa.Column(sa.ForeignKey('player.id'), primary_key=True)
    team_id   = sa.Column(sa.ForeignKey('team.id'), primary_key=True)

class UserAuthor(Base):
    '''
    Many-to-many connection table between user and author
    '''
    
    __tablename__ = 'user_author'
    
    user_id   = sa.Column(sa.ForeignKey('user.id'), primary_key=True)
    author_id = sa.Column(sa.ForeignKey('author.id'), primary_key=True)
    
    affinity  = sa.Column(sa.Float)
    
    user      = sa_orm.relationship('User', back_populates='author_affinities')
    author    = sa_orm.relationship('Author')    

class UserStrategy(Base):
    '''
    This class denotes the application of a strategy to a user for a
    specific period of time. Each strategy/user combination might appear
    more than once if a strategy applies to a user in two distinct periods
    '''
    
    __tablename__ = 'user_strategy'
    
    id          = sa.Column(sa.Integer, primary_key=True)
    user_id     = sa.Column(sa.ForeignKey('user.id'))
    strategy_id = sa.Column(sa.ForeignKey('strategy.id'))
    start_day   = sa.Column(sa.Integer)
    end_day     = sa.Column(sa.Integer)
    
    strategy    = sa_orm.relationship('Strategy', back_populates='users_assigned')
    user        = sa_orm.relationship('User', back_populates='strategies')

class UserTopic(Base):
    '''
    Many-to-many connection table between user and topic, including
    the user's interest for this topic
    '''
    
    __tablename__ = 'user_topic'
    
    user_id  = sa.Column(sa.ForeignKey('user.id'), primary_key=True)
    topic_id = sa.Column(sa.ForeignKey('topic.id'), primary_key=True)
    
    interest = sa.Column(sa.Float)
    
    user     = sa_orm.relationship('User', back_populates='topic_interests')
    topic    = sa_orm.relationship('Topic')



