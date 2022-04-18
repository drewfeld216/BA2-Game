from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, Boolean

from sqlalchemy.orm import registry, relationship, sessionmaker

# a sessionmaker(), also in the same scope as the engine
engine = create_engine('sqlite:///game.db')
Session = sessionmaker(engine)

mapper_registry = registry()
Base = mapper_registry.generate_base()

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
    authors = relationship('AuthorTopic', back_populates='topic')
    events = relationship('EventTopic', back_populates='topic')
    users = relationship('UserTopic', back_populates='topic')

class Event(Base):
    __tablename__ = 'event'
    id = Column(Integer, primary_key=True)
    start = Column(Integer)
    end = Column(Integer)
    intensity = Column(Integer)
    topics = relationship('EventTopic', back_populates='event')

class Author(Base):
    __tablename__ = 'author'
    id = Column(Integer,  primary_key=True)
    name = Column(String(50))
    quality = Column(Integer)
    popularity = Column(Integer)
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
    topic = relationship('Topic')
    author = relationship('Author')

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    ip = Column(String(20))
    agent = Column(String(100))
    freq = Column(Integer)
    first_day = Column(Integer)
    lifetime = Column(Integer)
    ad_sensitivity = Column(Float)
    topics = relationship('UserTopic', back_populates='user')
    authors = relationship('UserAuthor', back_populates='user')

class Pageview(Base):
    __tablename__ = 'pageview'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    article_id = Column(Integer, ForeignKey('article.id'))
    day = Column(Integer)
    duration = Column(Integer)
    saw_paywall = Column(Boolean)
    user = relationship('User')
    article = relationship('Article')

class Game(Base):
    __tablename__ = 'game'
    id = Column(Integer, primary_key=True)

class Team(Base):
    __tablename__ = 'team'
    id = Column(Integer, primary_key=True)

class Player(Base):
    __tablename__ = 'player'
    id = Column(Integer, primary_key=True)

def create_db():
    mapper_registry.metadata.drop_all(engine)
    mapper_registry.metadata.create_all(engine)