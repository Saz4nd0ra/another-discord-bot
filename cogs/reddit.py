import discord
from discord.ext import commands
from .utils import checks, embed, config
config = config.Config()
import praw import Reddit
import random

class API:
    def __init__(self):
        self.reddit = praw.Reddit(client_id=config.praw_clientid,
                     client_secret=config.praw_secret,
                     user_agent='another-discord-bot by /u/Saz4nd0ra')
        
    async def get_hot_submissions(self, subreddit: str):
        submission = self.reddit.subreddit(subreddit).hot(limit=3)
        return subreddit[random.randint(0,2)]

class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = API()

    @commands.group()
    async def browse(self, ctx, subreddit):
        """Get hot, new or best submissions from a specified subreddit."""
        submission = await self.api.get_hot_submissions(self, subreddit)

        embed = await embed.Embed(self.ctx.bot, self.ctx, description=foo, title=f'foor {bar}')
