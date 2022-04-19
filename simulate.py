from tqdm import tqdm
import random
import numpy as np
import pandas as pd
from scipy.stats import dirichlet, expon, uniform, norm
from faker import Faker
from sqlalchemy import select

from models import Session, create_db, Topic, Author, AuthorTopic, Event, EventTopic, Article, User, UserTopic, UserAuthor, Game, Team, Strategy
from metrics import get_metric

fake = Faker()

# Define some global parameters
N_DAYS = 365*2
N_DAYS_PERIOD_0 = 365
N_AUTHORS = 50
N_USERS = 1000

# Static definition of topics
TOPIC_NAMES = ['Opinion', 'Politics', 'World Events', 'Business', 'Technology', 'Arts & Culture', 'Sports', 'Health', 'Home', 'Travel', 'Fashion', 'Food']
TOPIC_ALPHAS = np.ones(len(TOPIC_NAMES))
TOPIC_PROBS = np.array([[0.1, 0.1, 0.1, 0.1, 0.08, 0.08, 0.08, 0.08, 0.08, 0.07, 0.07, 0.06]])

# 1. Topics DONE
# 2. Authors DONE
# 3. Events DONE
# 4. Articles DONE
# 5. Users DONE
# 6. Pageviews
# 7. Conversions

def generate_topics():
    # Define possible topics and baseline probabilities // right now all made up, but should be based on data eventually
    return zip(
        TOPIC_NAMES,
        TOPIC_PROBS[0],
    )

# Generate fake authors and probability vectors
def generate_authors():
    names = [fake.name() for i in range(N_AUTHORS)]
    quality = [uniform.rvs()*10 for i in range(N_AUTHORS)]
    topics = np.array([dirichlet.rvs(TOPIC_ALPHAS)[0] for auth in names])
    popularity = dirichlet.rvs(np.ones(N_AUTHORS)*10)[0]
    return zip(names, quality, popularity, topics)

class UserSession:
    def __init__(self, user_id, row, day, events, articles):
        # here a user will accumulate one or more pageviews.
        # each time a pageview is accumulated, the user and the pageview will be passed to a
        # strategy object, which will determine if the user will be asked to pay, and if not,
        # how many ads the user will show.
        self.user = row
        self.user.id = user_id
        # dummy return value showing struct of a pageview
    def pageview(article):
        pass
    def get_pageviews(self):
        return [{ 'article_id': 0, 'user_id': self.user.id, 'day': day, 'duration': 90 }] # duration is in seconds

# this has to have no memory so that we can use it during the simulation
def generate_pvs(start, end):
    with Session() as db:
        game = db.get(Game, 1) # TODO: Make this a parameter
        for day in tqdm(range(start, end)):
            # what events are live today?
            events_today = db.query(Event) \
                .where(Event.start <= day) \
                .where(Event.end >= day) \
                .where(Event.game_id == game.id) \
                .all()
            # what users are eligible to visit today?
            users_today = db.query(User) \
                .where(User.first_day <= day) \
                .where(day < User.first_day + User.lifetime) \
                .where(User.game_id == game.id) \
                .all()
            # what articles might they see?
            if (len(events_today)):
                longtail = min([e.start for e in events_today])
            else:
                longtail = day
            articles_today = db.query(Article) \
                .where(Article.day >= longtail) \
                .where(Article.day <= day) \
                .where(Article.game_id == game.id) \
                .all()
            
            for user in users_today:
                user.simulate_session(db, day, articles_today, True)
            pv_scores = get_metric('pv_score')
            db.commit()
        
        pv_scores = get_metric('pv_score')
        print(np.average(pv_scores))
        print(np.std(pv_scores))

def seed():
    create_db()
    with Session() as session:

        # TODO: move this into its own set of commands or interface
        game = Game(name='Test Game', seed=123) # TODO: Use this seed
        session.add(game)
        for t in ['austin', 'drew', 'daniel']:
            team = Team(name=t, game=game)
            session.add(team)
            strategy = Strategy(team=team, cost=7.99, ads=4, free_pvs=10)
            session.add(strategy)
        session.commit()

        topics = []
        authors = []
        print('Generating Topics')
        for topic_name, prob in generate_topics():
            t = Topic(name=topic_name, prob=prob, game=game)
            topics.append(t)
            session.add(t)
        session.commit()

        print('Generating Authors')
        for author_name, quality, popularity, topic_probs in generate_authors():
            a = Author(name=author_name, quality=quality, popularity=popularity, game=game)
            for topic, prob in zip(topics, topic_probs):
                tp = AuthorTopic(prob=prob)
                tp.topic = topic
                a.topics.append(tp)
            session.add(a)
            authors.append(a)
        session.commit()

        events = []
        intensities = [] # instrumented to add articles based on intensity

        print('Generating Events')
        for day in tqdm(range(N_DAYS)):
            # Generate new event with some probability (TBD)
            # Always at least one event
            for _ in range(0, max(1, int(norm.rvs(loc=3, scale=2)))):
                event_influence = dirichlet.rvs(TOPIC_ALPHAS)[0] # Concentration parameters TBD
                event_duration = expon.rvs(loc=0.01, scale=0.1) # some events should be long-lived
                duration_days = np.ceil(event_duration * 30)
                # hmm, event duration and intensity is generally correlated
                event_intensity = expon.rvs(scale=0.1, loc=0.1)
                evt = Event(
                    start=day,
                    end=day+duration_days,
                    intensity=event_intensity,
                    game=game,
                )
                for topic, prob in zip(topics, event_influence):
                    tp = EventTopic(prob=prob)
                    tp.topic = topic
                    evt.topics.append(tp)
                session.add(evt)
                events.append(evt)
        session.commit()
        
        print('Generating Articles')
        for day in tqdm(range(N_DAYS)):
            # Loop through events and sum topic probabilities of all active events
            day_topicsprobs = TOPIC_PROBS.copy()
            day_intensities = []
            for event in events:
                if event.start <= day and event.end >= day:
                    day_topicsprobs += event.intensity * np.asarray([t.prob for t in event.topics])
                    day_intensities.append(event.intensity)
            avg_intensity = np.average(day_intensities)
            intensities.append(avg_intensity)
            # # Normalize probabilities
            day_topicsprobs = day_topicsprobs[0] / day_topicsprobs[0].sum()
            
            # Generate articles for day
            # Intensity roughly varies between 0.14 and 0.31, so we add between 2 and 10 articles based on intensity
            n_articles = round(norm.rvs(loc=N_AUTHORS / 3, scale=N_AUTHORS / 10) + (avg_intensity**2 * 100))
            for _ in range(n_articles):
                article_topic = np.random.choice(topics, p=day_topicsprobs)
                # Normalize probabilities
                author_probs = np.asarray([a.topic_by_id(article_topic.id).prob for a in authors])
                author_probs = author_probs / author_probs.sum()
                article_author = np.random.choice(authors, p=author_probs)
                article = Article(
                    topic=article_topic,
                    author=article_author,
                    day=day,
                    game=game,
                    # better generated by more parameters? OK for now...
                    wordcount=int(max(10, norm.rvs(loc=50, scale=4), norm.rvs(loc=400, scale=200)))
                )
                session.add(article)
        session.commit()

        print('Generating Users')
        for _ in tqdm(range(N_USERS)):
            u = User(
                ip=fake.ipv4(),
                agent=fake.user_agent(),
                freq=max(int(norm.rvs(loc=5, scale=5)), 0),
                first_day=int(uniform.rvs()*N_DAYS),
                lifetime=int(expon.rvs(loc=20, scale=730)),
                ad_sensitivity = norm.rvs(loc=3, scale=1),
                game=game
            )
            prefs = dirichlet.rvs(TOPIC_ALPHAS)
            num_favorite = np.ceil(uniform.rvs()*4)
            for author in random.sample(authors, int(num_favorite)):
                u.authors.append(UserAuthor(author=author))
            for topic, prob in zip(topics, prefs[0]):
                u.topics.append(UserTopic(topic=topic, prob=prob))
            session.add(u)
        session.commit()