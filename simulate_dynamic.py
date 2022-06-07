import random, itertools

from models import UserStrategy, Pageview

# A Session is a visit to a site that might have one or more pageviews.
#
# The session simulator contains the logic to simulate the four events that drive the game:
#
# 1. Will a user start a session today?
# 2. If a user starts a session, how many articles will they read?
# 3. For each article, will the user hit the paywall?
# 4. If the user hits the paywall, will they become a paying subscriber?
#
# Will a user start a session? This is driven by three primary activities.
#
# -  A user is browsing social media and follows a link to an article. Twitter and Facebook are
#    both likely referral sources. Other social networks are a tiny fraction.
# -  A user encounters a search result from our publication and follows the link to read it. Google
#    is overwhelmingly the dominant referer. We count Google News as a search referer. We can also
#    count links from other news sources and other websites in this category; link referrals from
#    other publishers are an insignificant portion of traffic.
# -  Direct traffic, which is what we want most. Direct traffic to our homepage creates user habit
#    Few publications attain a high volume of direct traffic; those that do have a strong case for
#    building a subscription model.
#
# For our purposes, we can count traffic to our website and traffic to a mobile application as 
# interchangeable.
#
# Universally, the average pageviews per session is about 1.25. Getting a second pageview is
# regarded as a big win, and there's an entire sub-industry built around it. This is driven by
# search and social referers, where the primary activity the user is engaged with is connecting
# with friends or colleagues (social) or learning about a topic (search). In this way, people end up
# at websites that they would never pay money for. But when a user visits our site directly, the
# primary activity is engaging with the news and they are primed to pay.
#
# How many articles will they read?
# 
# The number of articles is driven almost entirely by interest in a particular topic, affinity for
# the publication, and the focus on the task at hand. Certainly users can change tasks from social
# or search, especially if they're casually browsing, but the purpose of the session plays a large
# part in determining how many articles they'll read. If they're looking to get a sense of the day's
# news, pages per session will be much higher than if they're following a link from a friend's
# Facebook account.
#
# Will a user hit the paywall?
#
# There's no randomness in this question, but it's an important piece of logic. A default set of
# logic which treats all users the same governs this during the initial period of the game, and
# teams can define this logic for themselves once they "take over" the publication and then into a
# final simulated stretch.
#
# Will the user pay?
#
# This is driven by income, media consumption proclivities, and affinity for the publication. In
# the real world, the strongest available predictor is the number of sessions over a period of time.
# Buying additional data around income and media proclivities adds considerable signal.
class SessionSimulator:
    def __init__(self, user, game):
        self.user = user
        self.game = game

    def topics_dict(self):
        td = {}
        for user_topic in self.user.topics:
            td[user_topic.topic.name] = user_topic.prob
        return td

    def pageview(self, db, score, day, article, team, prior_pvs):
        strategy = team.get_strategy_for_user(self.user, article, day)
        duration = article.wordcount / 230 * 2 * score # 230 wpm of reading
        saw_paywall = False
        converted = False
        user_strategy = self.user.teams \
            .filter(UserStrategy.team_id == team.id) \
            .first()
        if (not user_strategy):
            saw_paywall = (len(prior_pvs) >= strategy.free_pvs)
            if (saw_paywall):
                converted = random.random() > 0.1 # one in ten chance of converting
                if (converted):
                    db.add(UserStrategy(team=team, user=self.user, strategy=strategy, start_day=day))
        db.add(
            Pageview(
                team=team,
                article=article,
                day=day,
                duration=duration,
                ads_seen=strategy.ads,
                saw_paywall=saw_paywall,
                converted=converted,
                user=self.user,
            )
        )

    # This is the core of the dynamic logic which determines 
    def simulate_session(self, db, day, articles, cache_pvs = False):
        # sort articles by how much the user is likely to want to read
        user_topics = self.user.topics_dict()
        random.shuffle(articles)
        for team in self.game.teams:
            # For the first year simulation, we use a simple in-memory cache for pageviews
            # so it doesn't take an actual year to run the sim
            if (cache_pvs):
                articles_seen = pv_cache.get(team, self.user, 30)
            else:
                prior_pvs = self.user.pageviews \
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
                if (score > score_cutoff):
                    self.pageview(db, score, day, article, team, articles_seen)
                    articles_clicked.append(article.id)
                    # each subsequent article is harder to click
                    score_cutoff += score_stddev * 0.5
            pv_cache.append(team, self.user, articles_clicked)

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


# From simulate.py

# this has to have no memory so that we can use it during the simulation
def generate_pvs(game, start = 0, end = N_DAYS_PERIOD_0):
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