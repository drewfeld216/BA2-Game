import rand_utils

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm


import itertools
import random

import pandas as pd

from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, func, select
from sqlalchemy.orm import relationship

from metrics import log_metric

engine          = sa.create_engine('sqlite:///game.db')
Session         = sa_orm.sessionmaker(engine)

mapper_registry = sa_orm.registry()
Base            = mapper_registry.generate_base()

def run_sql(s):
    with engine.connect() as con:
        return pd.DataFrame(con.execute(s).fetchall())

# not an ORM wrapper
class BaseStrategy:
    cost = 9
    ads = 3
    free_pvs = 12

class AuthorTopic(Base):
    __tablename__ = 'author_topic'
    author_id = Column(ForeignKey('author.id'), primary_key=True)
    topic_id = Column(ForeignKey('topic.id'), primary_key=True)
    prob = Column(Float)
    author = relationship("Author", back_populates="topics")
    topic = relationship("Topic", back_populates="authors")

class EventTopic(Base):
    __tablename__ = ' event_topic'
    event_id = Column(ForeignKey('event.id'), primary_key=True)
    topic_id = Column(ForeignKey('topic.id'), primary_key=True)
    prob = Column(Float)
    event = relationship("Event", back_populates="topics")
    topic = relationship("Topic", back_populates="events")

class UserTopic(Base):
    __tablename__ = 'user_topic'
    user_id = Column(ForeignKey('user.id'), primary_key=True)
    topic_id = Column(ForeignKey('topic.id'), primary_key=True)
    prob = Column(Float)
    user = relationship("User", back_populates="topics")
    topic = relationship("Topic", back_populates="users")

# Doesn't strictly need to be defined as a model but it will be
# easier to add more signals on this relationship later if it is.
class UserAuthor(Base):
    __tablename__ = 'user_author'
    user_id = Column(ForeignKey('user.id'), primary_key=True)
    author_id = Column(ForeignKey('author.id'), primary_key=True)
    user = relationship("User", back_populates="authors")
    author = relationship("Author", back_populates="users")

class Topic(Base):
    __tablename__ = 'topic'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    prob = Column(Float)
    game_id = Column(ForeignKey('game.id'))
    game = relationship('Game')
    authors = relationship('AuthorTopic', back_populates='topic')
    events = relationship('EventTopic', back_populates='topic')
    users = relationship('UserTopic', back_populates='topic')

class Event(Base):
    __tablename__ = 'event'
    id = Column(Integer, primary_key=True)
    start = Column(Integer)
    end = Column(Integer)
    intensity = Column(Integer)
    game_id = Column(ForeignKey('game.id'))
    game = relationship('Game')
    topics = relationship('EventTopic', back_populates='event')

class Author(Base):
    __tablename__ = 'author'
    id = Column(Integer,  primary_key=True)
    name = Column(String(50))
    quality = Column(Integer)
    popularity = Column(Integer)
    game_id = Column(ForeignKey('game.id'))
    game = relationship('Game')
    topics = relationship('AuthorTopic', back_populates='author')
    users = relationship('UserAuthor', back_populates='author')

    def topic_by_id(self, topic_id):
        for t in self.topics:
            if t.topic_id == topic_id:
                return t

class Article(Base):
    __tablename__ = 'article'
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topic.id'))
    author_id = Column(Integer, ForeignKey('author.id'))
    day = Column(Integer)
    wordcount = Column(Integer)
    game_id = Column(ForeignKey('game.id'))
    game = relationship('Game')
    topic = relationship('Topic')
    author = relationship('Author')

class PVCache:
    teams = {}
    
    def get(self, team, user, trailing_days):
        try:
            return list(itertools.chain(*self.teams[team.id][user.id][-trailing_days:]))
        except:
            return []

    def append(self, team, user, articles):
        if team.id not in self.teams.keys():
            self.teams[team.id] = {}
        if user.id not in self.teams[team.id].keys():
            self.teams[team.id][user.id] = []
        self.teams[team.id][user.id].append(articles)

pv_cache = PVCache()

class User(Base):
    '''
    This class represents a single user, associated with one specific
    game
    '''
    
    __tablename__ = 'user'
    
    id             = sa.Column(sa.Integer, primary_key=True)
    game_id        = sa.Column(sa.ForeignKey('game.id'))
    
    # Basic attributes
    ip             = sa.Column(String(20))
    agent          = sa.Column(String(100))
    freq           = sa.Column(Integer)
    first_day      = sa.Column(Integer)
    lifetime       = sa.Column(Integer)
    ad_sensitivity = sa.Column(Float)
    ad_blocked     = sa.Column(Boolean)

    # Attributes that need to be purhcased
    age                  = sa.Column(sa.Integer)
    household_income     = sa.Column(sa.Integer)
    media_consumption    = sa.Column(sa.Integer)
    internet_usage_index = sa.Column(sa.Integer)

    game      = relationship('Game')
    topics    = relationship('UserTopic', back_populates='user')
    authors   = relationship('UserAuthor', back_populates='user')
    pageviews = relationship('Pageview', back_populates='user', lazy='dynamic')
    teams     = relationship('UserStrategy', back_populates='user', lazy='dynamic')

    def topics_dict(self):
        td = {}
        for user_topic in self.topics:
            td[user_topic.topic.name] = user_topic.prob
        return td

    def pageview(self, db, score, day, article, team, prior_pvs):
        strategy = team.get_strategy_for_user(self, article, day)
        duration = article.wordcount / 230 * 2 * score # 230 wpm of reading
        saw_paywall = False
        converted = False
        user_strategy = self.teams \
            .filter(UserStrategy.team_id == team.id) \
            .first()
        if (not user_strategy):
            saw_paywall = (len(prior_pvs) >= strategy.free_pvs)
            if (saw_paywall):
                converted = random.random() > 0.1 # one in ten chance of converting
                if (converted):
                    db.add(UserStrategy(team=team, user=self, strategy=strategy, start_day=day))
        db.add(
            Pageview(
                team=team,
                article=article,
                day=day,
                duration=duration,
                ads_seen=strategy.ads,
                saw_paywall=saw_paywall,
                converted=converted,
                user=self,
            )
        )

    def simulate_session(self, db, day, articles, cache_pvs = False):
        # sort articles by how much the user is likely to want to read
        user_topics = self.topics_dict()
        random.shuffle(articles)
        for team in self.game.teams:
            # For the first year simulation, we use a simple in-memory cache for pageviews
            # so it doesn't take an actual year to run the sim
            if (cache_pvs):
                articles_seen = pv_cache.get(team, self, 30)
            else:
                prior_pvs = self.pageviews \
                    .filter(Pageview.team_id == team.id) \
                    .filter(Pageview.day <= day) \
                    .filter(Pageview.day <= 30) \
                    .all()
                articles_seen = [pv.article.id for pv in prior_pvs]
            score_average = 0.25651818456545666
            score_stddev = 0.14619941832318883
            score_cutoff = score_average + score_stddev
            articles_clicked = []
            for article in articles:
                # don't click the same headline twice
                if article.id in articles_seen:
                    continue
                score = sum((
                    user_topics[article.topic.name] * 2,
                    article.author.popularity * 0.5,
                    article.author.quality * 0.02,
                ))
                log_metric('pv_score', score)
                if (score > score_cutoff):
                    self.pageview(db, score, day, article, team, articles_seen)
                    log_metric('pv_intent')
                    articles_clicked.append(article.id)
                    # each subsequent article is harder to click
                    score_cutoff += score_stddev * 0.5
            pv_cache.append(team, self, articles_clicked)

class Pageview(Base):
    '''
    This class represents a pageview in the came, associated with a
    specific user, article, and team (different teams might experience
    different views for the same article)
    '''
    
    __tablename__ = 'pageview'
    
    id          = sa.Column(Integer, primary_key=True)
    user_id     = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    article_id  = Column(Integer, sa.ForeignKey('article.id'))
    team_id     = Column(Integer, sa.ForeignKey('team.id'))
    day         = Column(Integer)
    duration    = Column(Integer)
    ads_seen    = Column(Integer)
    saw_paywall = Column(Boolean)
    converted   = Column(Boolean)
    
    user        = relationship('User')
    article     = relationship('Article')
    team        = relationship('Team')

class Game(Base, rand_utils.Rand_utils_mixin):
    '''
    This class describes a specific game.
    
    random_state holds the class' random state, and rand_utils.Rand_utils_mixin
    endows this object with a generate_rv method, which can be used for
    convenience to generate random variables and keep the random state up to date
    '''
    
    __tablename__ = 'game'
    
    id           = sa.Column(sa.Integer, primary_key=True)
    seed         = sa.Column(sa.Integer, nullable=False)
    name         = sa.Column(sa.String(50))
    
    random_state = sa.Column(sa.String(20000), default='')
    
    teams        = sa_orm.relationship('Team', back_populates='game')

    def __init__(self, **kwargs):
        '''
        First, initialize the class using __init__ in the super class.
        Then, initialize the random state using the seed
        '''
        super(Game, self).__init__(**kwargs)
        
        rand_utils.init_random_state(self)
    
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
    
    user        = sa_orm.relationship('User')
    strategy    = sa_orm.relationship('Strategy')

class Strategy(Base):
    '''
    This class describes a strategy. Each strategy belongs to a
    team, and can be applied to a number of users
    '''

    __tablename__ = 'strategy'
    
    id       = sa.Column(Integer, primary_key=True)
    team_id  = sa.Column(Integer, ForeignKey('team.id'))
    cost     = sa.Column(Float)
    ads      = sa.Column(Integer)
    free_pvs = sa.Column(Integer)
    
    team     = sa_orm.relationship('Team')

class PlayerTeam(Base):
    '''
    This class denotes the fact a player should have access to
    a specific team. It is a many-to-many association table
    '''
    
    __tablename__ = 'player_team'
    
    player_id = sa.Column(sa.ForeignKey('player.id'), primary_key=True)
    team_id   = sa.Column(sa.ForeignKey('team.id'), primary_key=True)

class Player(Base):
    '''
    Player email, hashed password, etc...
    '''
    
    __tablename__ = 'player'
    
    id              = sa.Column(sa.Integer, primary_key=True)
    email           = sa.Column(sa.String(50), nullable=False)
    hashed_password = sa.Column(sa.String(50), nullable=False)
    
    teams = sa_orm.relationship('Team', secondary='player_team', back_populates='players')

class Team(Base, rand_utils.Rand_utils_mixin):
    '''
    This class describes a specific team, in a specific game.
    
    Each team will have its own randomization engine, initialized with the same seed
    as the game randomization engine, to ensure that one team's actions do not in any
    way impact the random path that will be observed by another team.
    
    random_state holds the class' random state, and rand_utils.Rand_utils_mixin
    endows this object with a generate_rv method, which can be used for
    convenience to generate random variables and keep the random state up to date
    '''

    __tablename__ = 'team'
    
    id               = sa.Column(Integer, primary_key=True)
    name             = sa.Column(String(50))
    game_id          = sa.Column(Integer, ForeignKey('game.id'))
    
    random_state     = sa.Column(String(20000), default='')
    
    game             = sa_orm.relationship('Game', back_populates='teams')
    strategies       = sa_orm.relationship('Strategy', back_populates='team')
    players          = sa_orm.relationship('Player', back_populates='player_team', back_populates='teams')
    
    def __init__(self, **kwargs):
        '''
        First, initialize the class using __init__ in the super class.
        Then, initialize the random state using the parent game's seed
        '''
        super(Game, self).__init__(**kwargs)
        
        self.seed = self.game.seed
        rand_utils.init_random_state(self) 

def create_db():
    mapper_registry.metadata.drop_all(engine)
    mapper_registry.metadata.create_all(engine)