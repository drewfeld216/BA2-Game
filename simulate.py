import models as m
import simulate_static
from tqdm import tqdm




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




# game = m.Game(name='Test Game', seed=123, n_days=30*2, n_days_p0=30, n_authors=50, n_users=1000)

def initiate_game(game):
    TOPIC_NAMES = ['Opinion', 'Politics', 'World Events', 'Business', 'Technology', 'Arts & Culture', 'Sports', 'Health', 'Home', 'Travel', 'Fashion', 'Food']
    

    with m.Session() as db:
        # Create the topics
        # -----------------
        print('Generating topics')
        
        for t_name in TOPIC_NAMES:
            game.topics.append(m.Topic(name=t_name, game=game))
        
        db.commit()
        
        # Create the authors
        # ------------------
        print('Generating authors')
        
        for a in range(game.n_authors):
            author =  m.Author(name    = simulate_static.author_name(game),
                               quality = simulate_static.author_quality(game))
            game.authors.append(author)
            
            # Add author expertise for every topic
            for t in game.topics:
                author.topic_expertises.append(m.AuthorTopic(topic=t))
            
            simulate_static.add_author_expertises(author, game)
                    
        # Add author productivities
        simulate_static.add_author_productivities(game)
        
        db.commit()
        
        # Create the events
        # -----------------
        print('Generating events')
        
        for day in tqdm(range(game.n_days)):
            n_events = simulate_static.events_per_day(game)
            
            for _ in range(n_events):
                event = m.Event(start     = day,
                                intensity = simulate_static.event_intensity(game))
                game.events.append(event)
                
                # Add topic relevance for each topic
                for t in game.topics:
                    event.topic_relevances.append(m.EventTopic(topic=t))
                
                simulate_static.add_event_relevances(event, game)
        
        db.commit()
        
        # Create the articles
        # -------------------
        print('Generating articles')
        
        for day in tqdm(range(game.n_days)):
            # Find the articles that will be published
            articles = [simulate_static.event_articles(event, day)
                                                for event in game.events]
            
            # Simulate the articles
            game.articles.extend([m.Article(topic     = t,
                                            author    = simulate_static.article_author(t),
                                            wordcount = simulate_static.article_wordcount(game),
                                            vocab     = simulate_static.article_vocab(game))
                                                                for t in articles if i is not None])
            
        db.commit()
            
        # Create the users
        # ----------------
        print('Generating users')
        
        for _ in tqdm(range(game.n_users)):
            





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