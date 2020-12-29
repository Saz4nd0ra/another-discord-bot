import praw
from ...utils.config import Config
import random


class API:
    def __init__(self):

        self.config = Config()
        self.connection = praw.Reddit(
            client_id=self.config.praw_clientid,  # connecting to reddit using appilcation details and account details
            client_secret=self.config.praw_secret,
            password=self.config.praw_password,  # the actual password of the application account
            username=self.config.praw_username,  # the actual username of the application account
            user_agent="another-discord-bot by /u/Saz4nd0ra",
        )

    async def get_submission(self, subreddit: str, sorting: str):
        if sorting == "hot":
            submissions = self.connection.subreddit(subreddit).hot(limit=100)
        elif sorting == "new":
            submissions = self.connection.subreddit(subreddit).new(limit=3)
        else:
            submissions = self.connection.subreddit(subreddit).top(limit=100)

        post_to_pick = random.randint(1, 100)

        for x in range(0, post_to_pick):
            submission = next(x for x in submissions if not x.stickied)
        return submission

    async def get_submission_from_url(self, reddit_url: str):
        submission = self.connection.submission(url=reddit_url)
        return submission
