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


# Static definition of topics



# 1. Topics DONE
# 2. Authors DONE
# 3. Events DONE
# 4. Articles DONE
# 5. Users DONE
# 6. Pageviews
# 7. Conversions


# this has to have no memory so that we can use it during the simulation
def generate_pvs(start = 0, end = N_DAYS_PERIOD_0):
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

#game = m.Game(name='Test Game', seed=123)

def initiate_game(game):
    TOPIC_NAMES = ['Opinion', 'Politics', 'World Events', 'Business', 'Technology', 'Arts & Culture', 'Sports', 'Health', 'Home', 'Travel', 'Fashion', 'Food']
    TOPIC_FREQS = [0.1, 0.1, 0.1, 0.1, 0.08, 0.08, 0.08, 0.08, 0.08, 0.07, 0.07, 0.06]
    
    topic_affinities = np.ones(len(TOPIC_NAMES))*0.2
    
    
    #n_days = 30*2
    #n_days_period_0 = 30
    #n_authors = 50
    #n_users = 1000

    with m.Session() as db:
        # Create the topics
        # -----------------
        print('Generating topics')
        
        for t_name, t_freq in zip(TOPIC_NAMES, TOPIC_FREQS):
            game.topics.append(m.Topic(name=t_name, freq=t_freq, game=game))
        
        db.commit()
        
        # Create the authors
        # ------------------
        print('Generating authors')
        
        author_popularities = game.generate_rv('dirichlet', alpha=np.ones(game.n_authors))
        
        for a in range(game.n_authors):
            author =  m.Author(name    = simulate_static.author_name(game),
                                         quality = simulate_static.author_quality(game))
            game.authors.append(author)
            
            # Add author expertise for every topic
            for t in range(game.topics):
                author.topic_expertises.append(m.AuthorTopic(topic=t))
            
            # Generate the expertises for that author
            simulate_static.add_author_expertises(author, game)
                                         
        # Add author productivities
        simulate_static.add_author_productivities(game)
        
        db.commit()
        
        


        
            # Add topic affinities
            for t, affinity in zip(game.topics,
                                     game.generate_rv('dirichlet', alpha=topic_affinities)):
                db.add(m.AuthorTopic(topic=t, author=author, affinity=affinity))
            
        db.commit()
        
        # Create the events
        # -----------------
        print('Generating events')
        for day in tqdm(range(game.n_days)):
            # Generate 0, 1, 2, or 3 events for this day.
            for _ in range(m.Event.g_events_per_day(game)):
                # Calibrate the intensity so that the most likely density is 1.
                # The intensity decreases all the way down to a maximum of 10,
                # where we observe a small bump because of rounding
                
                event = m.Event(start     = day,
                                intensity = m.Event.g_event_intensity(game),
                                game      = game)
                db.add(event)
                
                # Add topic affinities
                for t, relevance in m.EventTopic.g_event_topic_relevance(game):
                    db.add(m.EventTopic(topic=t, event=event, affinity=relevance))
                
        db.commit()
        
        # Create articles
        # ---------------
        print('Generating articles')
        for day in tqdm(range(game.n_days)):
            
        
        

def seed():
    create_db()
    with Session() as session:

        # TODO: move this into its own set of commands or interface
        game = Game(name='Test Game', seed=123) # TODO: Use this seed
        session.add(game)
        for t in ['austin', 'drew']:
            team = Team(name=t, game=game)
            session.add(team)
            strategy = Strategy(team=team, cost=7.99, ads=4, free_pvs=10)
            session.add(strategy)
        session.commit()

        

        events = []
        intensities = [] # instrumented to add articles based on intensity

        
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