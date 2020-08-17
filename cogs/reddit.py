import discord
from discord.ext import commands
from .utils import checks, config
config = config.Config()
from .utils.embed import SimpleEmbed
import praw
from praw import Reddit
import random

# TODO all of that

class Reddit(commands.Cog):
    """Browse reddit with those commands."""
    def __init__(self, bot):
        self.bot = bot
        self.reddit = praw.Reddit(client_id=config.praw_clientid, # connecting to reddit, read-only should be enough for our use
                     client_secret=config.praw_secret,
                     user_agent='another-discord-bot by /u/Saz4nd0ra')
        
    async def get_hot_submission(self, subreddit: str):
        submissions = self.reddit.subreddit(subreddit).hot(limit=100)
        post_to_pick = random.randint(1, 100)
        for x in range(0, post_to_pick):
            submission = next(x for x in submissions if not x.stickied)
        return submission

    @commands.group()
    async def browse(self, ctx):
        """Browses reddit."""
        pass

    @browse.command()
    async def meme(self, ctx, category = None):
        """Get the hottest memes from a specifif category.
        Available categories: 
        """
        if category == None: # if user doesn't provide a subreddit r/memes is the fallback subreddit
            submission = await self.get_hot_submission(self, subreddit='memes')
            e = SimpleEmbed(
                title = f'``Title :`` {submission.title}'
            )
            e.set_image(url=f'{submission.url}')
            e.add_field(name=':thumbsup: **Upvotes** :',value= f'{submission.ups}',inline=True)
            e.add_field(name=':envelope: **Comments** :',value= f'{len(submission.comments)}',inline=True)
            await ctx.send(embed=e)

        else: # use userprovided subreddit

            switcher = { # why isn't there a built in switch function yet?
                'anime': 'animemes',
                'dank': 'dankmemes'
                    # TODO implement more subreddits
                }

            subreddit_submissions = await self.get_hot_submissions(self, switcher.get(category))
            post_to_pick = random.randint(1, 100)
            for x in range(0, post_to_pick):
                submission = next(x for x in memes_submissions if not x.stickied)

    @browse.command()
    async def hot(self, ctx, subreddit: str):
        """Browse hot submission in a subreddit."""
        submission = await self.get_hot_submission(self, subreddit='memes')
        
def setup(bot):
    bot.add_cog(Reddit(bot))