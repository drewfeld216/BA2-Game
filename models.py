import numpy as np
from faker import Faker
import json





import itertools
import random

import pandas as pd

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, Boolean, func, select
from sqlalchemy.orm import registry, relationship, sessionmaker

from metrics import log_metric

engine = create_engine('sqlite:///game.db')
Session = sessionmaker(engine)

mapper_registry = registry()
Base = mapper_registry.generate_base()

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
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    ip = Column(String(20))
    agent = Column(String(100))
    freq = Column(Integer)
    first_day = Column(Integer)
    lifetime = Column(Integer)
    ad_sensitivity = Column(Float)
    ad_blocked = Column(Boolean)

    # gotta buy these
    age = Column(Integer)
    household_income = Column(Integer)
    media_consumption = Column(Integer)
    internet_usage_index = Column(Integer)

    game_id = Column(ForeignKey('game.id'))
    game = relationship('Game')
    topics = relationship('UserTopic', back_populates='user')
    authors = relationship('UserAuthor', back_populates='user')
    pageviews = relationship('Pageview', back_populates='user', lazy='dynamic')
    teams = relationship('UserStrategy', back_populates='user', lazy='dynamic')

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
    __tablename__ = 'pageview'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    article_id = Column(Integer, ForeignKey('article.id'))
    team_id = Column(Integer, ForeignKey('team.id'))
    day = Column(Integer)
    duration = Column(Integer)
    ads_seen = Column(Integer)
    saw_paywall = Column(Boolean)
    converted = Column(Boolean)
    user = relationship('User')
    article = relationship('Article')
    team = relationship('Team')

class Game(Base):
    '''
    This class describes a specific game. In addition to trivial
    game details, it includes the game's randomization engine,
    which works as follows
      - When the game is created, a seed is provided
      - The np random number generator (used by np) and the random
        random number generator (used by faker) are initialized
        with that seed
      - The state of both random number generators are serialized
        into the database (columns np_state and random_state
        respectively)
      - Whenever a random number needs to be generated for the game,
        the generate_rv function should be used - it loads the
        serialized state from the database, generated the RVs, and
        then saves the new state back. This ensures that even if
        other RVs are generated outside the class, we "pick up" again
        from where we left of the last time we ran generate_rv
    '''
    __tablename__ = 'game'
    
    id           = Column(Integer, primary_key=True)
    seed         = Column(Integer)
    name         = Column(String(50))
                 
    np_state     = Column(String(10000), default='')
    random_state = Column(String(10000), default='')
    
    teams        = relationship('Team', back_populates='game')
    
    fake         = Faker()
    
    def __init__(self, **kwargs):
        '''
        First, initialize the class using __init__ in the super class.
        Then, set the numpy and random seeds to the specified seed, and
        save the state of the generators into the database
        '''
        super(Game, self).__init__(**kwargs)
        
        # Set the numpy and faker random seeds
        np.random.seed(self.seed)
        self.fake.random.seed(self.seed)
        
        # Save the state of both randomization techniques into
        # the database
        self.save_random_state()
        
    def save_random_state(self):
        '''
        This function takes the current state of the numpy and random
        random number generators, serializes them, and save them into
        the database
        '''
        
        # Save the np state (note that np_state[1] is an ndarray which
        # can't be serialized, so we need to convert it to a list
        # first
        np_state      = list(np.random.get_state())
        np_state[1]   = np_state[1].tolist()
        self.np_state = json.dumps(np_state)
        
        # Save the random state
        self.random_state = json.dumps(self.fake.random.getstate())
    
    def load_random_state(self):
        '''
        This function takes the state of the numpy and random random
        number generators in the database, and uses them to set the
        current state of these generators
        '''
        
        # Load the np state from the database and set it
        np.random.set_state(json.loads(self.np_state))
        
        # Load the random state from the database and set it
        # (setstate requires the second element to be a tuple, hence
        # our conversion
        random_state    = json.loads(self.random_state)
        random_state[1] = tuple(random_state[1])
        self.fake.random.setstate(random_state)
    
    def generate_rv(self, kind, n=1, **kwargs):
        '''
        This function loads the current state of the random number
        generators from the database, generates the variables we
        need, and then saves the new state back. This ensures that
        even if other random variables were generated outside this
        function since the last time it was called, we always pick
        up again from the last time it was called
        
        To make sure we don't upset any operations outside this
        class, we save the random states before the function runs,
        and then reset them at the end
        '''
        
        # Dictionary mapping each variable type to a function
        # which generates that RV
        rv_kinds = {'uniform'     : lambda                : np.random.uniform(size=n),
                    'exponential' : lambda loc=0, scale=1 : np.random.exponential(size=n)*scale + loc,
                    'normal'      : lambda loc=0, scale=1 : np.random.normal(loc=loc, scale=scale, size=n),
                    'dirichlet'   : lambda alpha          : np.random.dirichlet(alpha=alpha, size=n),
                    'name'        : lambda                : [self.fake.name() for i in range(n)],
                    'ipv4'        : lambda                : [self.fake.ipv4() for i in range(n)],
                    'user_agent'  : lambda                : [self.fake.user_agent() for i in range(n)]}
    
        # Save the random state so we can restore it afterwards
        np_state     = np.random.get_state()
        random_state = self.fake.random.getstate()
    
        # Load the random state
        self.load_random_state()
        
        # Generate the RV
        out = rv_kinds[kind](**kwargs)
        
        # If the size is 1, extract the first element in the
        # list/array to return a scalar
        if n == 1:
            out = out[0]
        
        # Save the random state
        self.save_random_state()
        
        # Restore the original random state
        np.random.set_state(np_state)
        self.fake.random.setstate(random_state)
        
        # Return
        return out

class Team(Base):
    __tablename__ = 'team'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    game_id = Column(Integer, ForeignKey('game.id'))
    game = relationship('Game')
    strategies = relationship('Strategy', back_populates='team')
    classified_users = relationship('UserStrategy', back_populates='team')

    def get_strategy_for_user(self, user, article, day):
        return self.strategies[0] # TODO: Strategy management

class UserStrategy(Base):
    __tablename__ = 'user_strategy'
    team_id = Column(Integer, ForeignKey('team.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    strategy_id = Column(Integer, ForeignKey('strategy.id'))
    start_day = Column(Integer)
    end_day = Column(Integer) # not planning churn for now but tbd
    team = relationship('Team')
    user = relationship('User')
    strategy = relationship('Strategy')

class Strategy(Base):
    __tablename__ = 'strategy'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('team.id'))
    cost = Column(Float)
    ads = Column(Integer)
    free_pvs = Column(Integer)
    team = relationship('Team')

class Player(Base):
    __tablename__ = 'player'
    email = Column(String(50))
    id = Column(Integer, primary_key=True)

def create_db():
    mapper_registry.metadata.drop_all(engine)
    mapper_registry.metadata.create_all(engine)