import numpy as np
import pandas as pd
import datetime
from scipy.stats import dirichlet, expon, uniform, norm
from faker import Faker
fake = Faker()

# Helper to evaluate simulation output
def summary_stats(events, articles):
	events_df = pd.DataFrame(events)
	articles_df = pd.DataFrame(articles)
	
	
	print('Average Event Duration:')
	print(events_df.agg({"duration": "mean"}))
	
	print('Total Articles:')
	print(articles_df.agg({"id": "count"}))
	
	print('Article Count per Topic:')
	print(articles_df.groupby('topic', as_index=False).agg({"id": ["count", lambda x: x.count()/len(articles_df)*100]}))

# Define some global parameters
START_DATE = datetime.datetime(2021, 1, 1, 0, 0, 0)
N_DAYS = 365*2
N_AUTHORS = 50
N_USERS = 1000

# Define possible topics and baseline probabilities // right now all made up, but should be based on data eventually
topics = ['Opinion', 'Politics', 'World Events', 'Business', 'Technology', 'Arts & Culture', 'Sports', 'Health', 'Home', 'Travel', 'Fashion', 'Food']
topics_probs = np.array([[0.1, 0.1, 0.1, 0.1, 0.08, 0.08, 0.08, 0.08, 0.08, 0.07, 0.07, 0.06]])

# Generate fake authors and probability vectors
authors_names = [fake.name() for i in range(N_AUTHORS)]

alphas = np.ones(len(topics)) # Concentration parameters TBD, right now uniform
authors_topicsprobs = np.array([dirichlet.rvs(alphas)[0] for auth in authors_names])

events = []
# Generate events at random intervals
curr_time = START_DATE
while curr_time <= START_DATE + datetime.timedelta(days=N_DAYS):
	curr_time = curr_time + datetime.timedelta(days=expon.rvs(scale=1))
	
	# Generate new event with some probability (TBD)
	event_influence = dirichlet.rvs(alphas) # Concentration parameters TBD
	event_duration = round(expon.rvs(scale=3))
	event_intensity = expon.rvs(scale=0.1)
	events.append({'id': len(events), 'start': curr_time, 'influence': event_influence, 'duration': event_duration, 'intensity': event_intensity})

articles = []
# Loop through days and generate all articles
for day in range(N_DAYS):	
	# Loop through events and sum topic probabilities of all active events
	day_topicsprobs = topics_probs.copy()
	for event in events:
		if event['start'] + datetime.timedelta(days=event['duration']) >= START_DATE + datetime.timedelta(days=day):
			day_topicsprobs += event['intensity']*event['influence']	
	
	# Normalize probabilities
	day_topicsprobs = day_topicsprobs[0] / day_topicsprobs[0].sum()
	
	# Generate articles for day
	n_articles = round(norm.rvs()*4 + 20)
	for i in range(n_articles):
		article_topic = np.random.choice(topics, p=day_topicsprobs)
		# Normalize probabilities
		author_probs = authors_topicsprobs[:, topics.index(article_topic)]
		author_probs = author_probs / author_probs.sum()
		article_author = np.random.choice(authors_names, p=author_probs)
		articles.append({'id': len(articles), 'day': day, 'topic': article_topic, 'author': article_author})
		
summary_stats(events, articles)

# Generate users
users = []
for user in range(N_USERS):
	ip = fake.ipv4()
	agent = fake.user_agent()
	prefs = dirichlet.rvs(alphas)
	users.append({'ip': ip, 'agent': agent, 'prefs': prefs})
	
print(pd.DataFrame(users))

	