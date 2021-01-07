import praw
from .config import Config
import random
from rule34 import Rule34
from pybooru import Danbooru
import asyncio
from saucenao_api import SauceNao

VIDEO_FORMATS = [
    "mp4",
    "webm",
    # and so on, I don't really know which formats r34 uses
]


class RedditAPI:
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


class Rule34API:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.rule34 = Rule34(self.loop)

    async def get_random_r34(self, search):

        images = await self.rule34.getImages(tags=search)
        try:
            file = images[random.randint(0, len(images) - 1)]
        except TypeError:
            return

        if any(x in file.file_url for x in VIDEO_FORMATS):
            is_video = True
        else:
            is_video = False

        if file.source:
            has_source = True
        else:
            has_source = False

        return file, is_video, has_source


class DanbooruAPI:
    def __init__(self):
        self.danbooru = Danbooru("danbooru")

    def get_random_danbooru(self, search):

        images = self.danbooru.post_list(tags=search, limit=100)

        try:
            file = images[random.randint(0, len(images) - 1)]
        except TypeError:
            return

        if any(x in file["file_url"] for x in VIDEO_FORMATS):
            is_video = True
        else:
            is_video = False

        if file["source"]:
            has_source = True
        else:
            has_source = False

        return file, is_video, has_source


class SauceNaoAPI:
    def __init__(self):
        self.saucenao = SauceNao()

    def get_sauce_from_url(self, url):
        results = self.saucenao.from_url(url)

        return results[0]

    def get_sauce_from_file(self, file):
        results = self.saucenao.from_file(file)

        return results[0]
