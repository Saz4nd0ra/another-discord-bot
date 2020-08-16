import discord
from discord.ext import commands
from .utils import checks, config
config = config.Config()
from .utils.embed import SimpleEmbed
import praw
from praw import Reddit
import random

class API:
    def __init__(self):
        self.reddit = praw.Reddit(client_id=config.praw_clientid,
                     client_secret=config.praw_secret,
                     user_agent='another-discord-bot by /u/Saz4nd0ra')
        
    async def get_hot_submissions(self, subreddit: str):
        submissions = self.reddit.subreddit(subreddit).hot(limit=100)
        return submissions

class Reddit(commands.Cog):
    """Browse reddit with those commands."""
    def __init__(self, bot):
        self.bot = bot
        self.api = API()

    @checks.is_admin()
    @commands.group()
    async def browse(self, ctx):
        """Browses reddit."""
        pass

    @commands.command()
    async def meme(self, ctx, subreddit = None):

        if subreddit == None: # if user doesn't provide a subreddit r/memes is the fallback subreddit

            memes_submissions = await self.api.get_hot_submissions(self, subreddit='memes')
            post_to_pick = random.randint(1, 100)
            for x in range(0, post_to_pick):
                submission = next(x for x in memes_submissions if not x.stickied)
            e = SimpleEmbed(
                title = f'``Title :`` {submission.title}'
            )
            e.set_image(url=f'{submission.url}')
            e.add_field(name=':thumbsup: **Upvotes** :',value= f'{submission.ups}',inline=True)
            e.add_field(name=':envelope: **Comments** :',value= f'{len(submission.comments)}',inline=True)
            await ctx.send(embed=embed)

        else: # use userprovided subreddit

            subreddit_submissions = await self.api.get_hot_submissions(self, subreddit)
            post_to_pick = random.randint(1, 100)
            for x in range(0, post_to_pick):
                submission = next(x for x in memes_submissions if not x.stickied)

def setup(bot):
    bot.add_cog(Reddit(bot))