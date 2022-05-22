import rand_utils

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm


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

# -----------------------------
# -  Section 0 - terminology  -
# -----------------------------

'''
This section summarizes terminology we need to be consistent with:
  - Author
      * quality      : how good the author is
      * productivity : the likelihood an author will write an
                       article
  - Event
      * intensity    : the higher the intensity, the longer the event
                       and the stronger its impact on likely articles
  - Topic
      * suitability : the likelihood a specific topic will appear in our
                      publication
  - Author <> Topic
      * expertise   : the likelihood an author will write on a
                      specific topic
  - Event<>Topic
      * relevance   : the likelihood an event will lead to an article
                      about a specific topic
  - User <> Topic
      * interest    : the likelihood a user will read an article on a
                      specific topic
  - User <> Author
      * affinity    : the likelihood a user will want to read an article
                      by a specific author
  
'''

# ---------------------------------
# -  Section 1; base elements     -
# -  (Alphabetical by class name) -
# ---------------------------------

class Article(Base):
    '''
    A specific article, associated with a game
      - topic_id  : the topic the article is about
      - author_id : the author who wrote the article
      - day       : the day on which the article was published
      - wordcount : the number of words in the article
      - vocab     : a score between 0 and 1 indicating the complexity
                    of the vocabulary in this article
    '''
    
    __tablename__ = 'article'
    
    id        = sa.Column(sa.Integer, primary_key=True)
    game_id   = sa.Column(sa.ForeignKey('game.id'))
    topic_id  = sa.Column(sa.ForeignKey('topic.id'))
    author_id = sa.Column(sa.ForeignKey('author.id'))
    
    day       = sa.Column(sa.Integer)
    wordcount = sa.Column(sa.Integer)
    vocab     = sa.Column(sa.Integer)
    
    game      = sa_orm.relationship('Game')
    topic     = sa_orm.relationship('Topic')
    author    = sa_orm.relationship('Author')
    
class Author(Base):
    '''
    A specific author, associated with a game
      - quality : the quality of the author, a number between
                  0 and 10
      - productivity : the productivity of the author (i.e., how
            often they write articles). These are expressed as
            the probability THIS author will write an article if
            *any* author will write an article, so the productivities
            sum to 1 over all authors
      
    This author will generally have more interest in some topics
    than others. These relationships will be captured by rows in
    author_topic
    '''
    
    __tablename__ = 'author'
    
    id                = sa.Column(sa.Integer,  primary_key=True)
    game_id           = sa.Column(sa.ForeignKey('game.id'))
    name              = sa.Column(sa.String(50))
    quality           = sa.Column(sa.Integer)
    productivity      = sa.Column(sa.Integer)
    
    game              = sa_orm.relationship('Game', back_populates='authors')
    topic_expertises  = sa_orm.relationship('AuthorTopic', back_populates='author')

    def topic_by_id(self, topic_id):
        for t in self.topics:
            if t.topic_id == topic_id:
                return t

class Event(Base):
    '''
    A specific event, associated with a game. Attributes:
      - start     : the day on which the event begins
      - intensity : the intensity of the event; this will be a number
                    between 1 and 10. The higher the intensity, the
                    longer the event and the more pronounced its effect
                    (see topic_intensities method)
      - game_id   : the game the event belongs to

    Events are likely to lead to articles on specific topics
    with varying probabilities, captured by rows in event_topic
    '''

    __tablename__ = 'event'
    
    id                = sa.Column(sa.Integer, primary_key=True)
    start             = sa.Column(sa.Integer)
    intensity         = sa.Column(sa.Integer)
    game_id           = sa.Column(sa.ForeignKey('game.id'))
    
    game              = sa_orm.relationship('Game', back_populates='events')
    topic_relevances  = sa_orm.relationship('EventTopic',back_populates='event')
    
    def topic_intensities(self, day):
        '''
        Given a specific day, this function will return a
        dictionary, in which
          - Each key is a topic_id
          - Each value gives the impact of this event on the topic,
            taking into account
              (1) The intensity
              (2) The time since the start of the event
              
        The higher the intensity, the longer the event has an impact,
        and the stronger that impact.
        '''
        
        if day < self.start:
            # The event hasn't happened yet - the impact on every
            # topic is 0
            return {i.topic.id:0 for i in self.topic_relevances}
        else:
            # The higher the intensity, the longer the effect
            time_effect = np.exp(-(day - self.start)/self.intensity)
            
            # If the effect is smaller than 0.05 (more than 2 days after
            # an event of intensity 1), set it to 0
            time_effect = 0 if time_effect <= 0.05 else time_effect
            
            return {i.topic.id:self.intensity*time_effect*i.relevance
                                            for i in self.topic_relevances}
        
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

    def __init__(self, **kwargs):
        '''
        First, initialize the class using __init__ in the super class.
        Then, initialize the random state using the seed
        '''
        super(Game, self).__init__(**kwargs)
        
        rand_utils.init_random_state(self)

class Pageview(Base):
    '''
    This class represents a pageview in the came, associated with a
    specific user, article, and team (different teams might experience
    different views for the same article)
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
    Player email, hashed password, etc...
    '''
    
    __tablename__ = 'player'
    
    id              = sa.Column(sa.Integer, primary_key=True)
    email           = sa.Column(sa.String(50), nullable=False)
    hashed_password = sa.Column(sa.String(50), nullable=False)
    
    teams = sa_orm.relationship('Team', secondary='player_team', back_populates='players')

class Strategy(Base):
    '''
    This class describes a strategy. Each strategy belongs to a
    team, and can be applied to a number of users
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
    This class describes a specific team, in a specific game.
    
    Each team will have its own randomization engine, initialized with the same seed
    as the game randomization engine, to ensure that one team's actions do not in any
    way impact the random path that will be observed by another team.
    
    random_state holds the class' random state, and rand_utils.Rand_utils_mixin
    endows this object with a generate_rv method, which can be used for
    convenience to generate random variables and keep the random state up to date
    '''

    __tablename__ = 'team'
    
    id               = sa.Column(sa.Integer, primary_key=True)
    name             = sa.Column(sa.String(50))
    game_id          = sa.Column(sa.ForeignKey('game.id'))
    
    random_state     = sa.Column(sa.String(20000), default='')
    
    game             = sa_orm.relationship('Game', back_populates='teams')
    strategies       = sa_orm.relationship('Strategy', back_populates='team')
    players          = sa_orm.relationship('Player', secondary='player_team', back_populates='teams')
    
    def __init__(self, **kwargs):
        '''
        First, initialize the class using __init__ in the super class.
        Then, initialize the random state using the parent game's seed
        '''
        super(Team, self).__init__(**kwargs)
        
        self.seed = self.game.seed
        rand_utils.init_random_state(self) 

class Topic(Base):
    '''
    A specific topic, associated with a game
       - name : the name of the topic
       - freq : 
    '''
    
    __tablename__ = 'topic'
    
    id                = sa.Column(sa.Integer, primary_key=True)
    game_id           = sa.Column(sa.ForeignKey('game.id'))
    name              = sa.Column(sa.String(50))
    freq              = sa.Column(sa.Float)
    
    game              = sa_orm.relationship('Game', back_populates='topics')

class User(Base):
    '''
    This class represents a single user, associated with one specific
    game. Each user also has affinity relationships with topics and
    authors
    '''
    
    __tablename__  = 'user'
    
    id             = sa.Column(sa.Integer, primary_key=True)
    game_id        = sa.Column(sa.ForeignKey('game.id'))
    
    # Basic attributes
    ip             = sa.Column(sa.String(20))
    agent          = sa.Column(sa.String(100))
    freq           = sa.Column(sa.Integer)
    first_day      = sa.Column(sa.Integer)
    lifetime       = sa.Column(sa.Integer)
    ad_sensitivity = sa.Column(sa.Float)
    ad_blocked     = sa.Column(sa.Boolean)

    # Attributes that need to be purhcased
    age                  = sa.Column(sa.Integer)
    household_income     = sa.Column(sa.Integer)
    media_consumption    = sa.Column(sa.Integer)
    internet_usage_index = sa.Column(sa.Integer)

    game              = sa_orm.relationship('Game')
    topic_interests   = sa_orm.relationship('UserTopic', back_populates='user')
    author_affinities = sa_orm.relationship('Author', secondary='user_author')
    pageviews         = sa_orm.relationship('Pageview', back_populates='user', lazy='dynamic')
    strategies        = sa_orm.relationship('UserStrategy', back_populates='user')

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
    
    Might later include user-author affinities
    '''
    
    __tablename__ = 'user_author'
    
    user_id   = sa.Column(sa.ForeignKey('user.id'), primary_key=True)
    author_id = sa.Column(sa.ForeignKey('author.id'), primary_key=True)

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

# ---------------------------
# -  Section 3; PV cache    -
# ---------------------------

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