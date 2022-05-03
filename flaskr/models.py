import itertools
import random

from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, func, select
from sqlalchemy.orm import registry, relationship, sessionmaker, scoped_session
from flaskr.db import Base

from flaskr.functions.metrics import log_metric

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
    game_id = Column(ForeignKey('game.id'))
    game = relationship('Game')
    topics = relationship('UserTopic', back_populates='user')
    authors = relationship('UserAuthor', back_populates='user')
    pageviews = relationship('Pageview', back_populates='user', lazy='dynamic')

    def topics_dict(self):
        td = {}
        for user_topic in self.topics:
            td[user_topic.topic.name] = user_topic.prob
        return td

    def pageview(self, db, score, day, article, team, prior_pvs):
        strategy = team.get_strategy_for_user(self, article, day)
        duration = article.wordcount / 230 * 2 * score # 230 wpm of reading
        saw_paywall = (len(prior_pvs) >= strategy.free_pvs)
        converted = False
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
    __tablename__ = 'game'
    id = Column(Integer, primary_key=True)
    seed = Column(Integer)
    name = Column(String(50))
    teams = relationship('Team', back_populates='game')

class Team(Base):
    __tablename__ = 'team'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    game_id = Column(Integer, ForeignKey('game.id'))
    game = relationship('Game')
    strategies = relationship('Strategy', back_populates='team')
    classified_users = relationship('UserStrategy', back_populates='team')

    def get_strategy_for_user(self, user, article, day):
        return BaseStrategy() # TODO: Strategy management

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
    password = Column(String(50))
    type = Column(String(20))
    status = Column(String(20))
    id = Column(Integer, primary_key=True)

