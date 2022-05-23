# From Class User
# ---------------

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