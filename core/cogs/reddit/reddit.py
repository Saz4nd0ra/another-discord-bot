import discord
from ...utils import context
from discord.ext import commands
from ...utils.embed import Embed
import praw
from praw import Reddit
import random


# TODO all of that

REDDIT_DOMAINS = [
    "reddit.com",
    "redd.it",
]  # need to find more domains, if there are any


class RedditCog(commands.Cog):
    """Browse reddit with those commands."""

    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
        self.voting_message = None
        self.reactions = {"↑": "upvote", "↓": "downvote"}
        self.reddit = praw.Reddit(
            client_id=self.config.praw_clientid,  # connecting to reddit using appilcation details and account details
            client_secret=self.config.praw_secret,
            password=self.config.praw_password,  # the actual password of the application account
            username=self.config.praw_username,  # the actual username of the application account
            user_agent="another-discord-bot by /u/Saz4nd0ra",
        )

    async def get_submission(self, subreddit: str, sorting: str):
        if sorting == "hot":
            submissions = self.reddit.subreddit(subreddit).hot(limit=100)
        if sorting == "new":
            submissions = self.reddit.subreddit(subreddit).new(limit=3)
        else:
            submissions = self.reddit.subreddit(subreddit).top(limit=100)

        post_to_pick = random.randint(1, 100)

        for x in range(0, post_to_pick):
            submission = next(x for x in submissions if not x.stickied)
        return submission

    async def get_submission_from_url(self, url: str):
        submission = self.reddit.submission(url)
        return submission

    async def upvote_post(self):
        pass

    async def downvote_post(self):
        pass

    async def build_embed(self, ctx, submission):
        """Embed that includes a voting system."""

        e = Embed(ctx, title=f"Title: {submission.title}", image=submission.url)
        e.add_fields(
            (":thumbsup: **Upvotes**:", f"{submission.ups}"),
            (":envelepe: **Comments**:", f"{len(submission.comments)}"),
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        """Catch reddit links, check them, and then return them as a nice embed."""
        ctx = await self.bot.get_context(message, cls=context.Context)
        if any(x in message.content for x in REDDIT_DOMAINS):
            submission_url = message.content
            submission = await self.get_submission_from_url(url=submission_url)
            if submission.over_18 is True and message.channel.is_nsfw() is not True:
                await message.delete()
                await ctx.send(
                    f"{message.author.mention} this channel doesn't allow NSFW."
                )
            else:
                await self.reddit_embed(ctx, submission)

    @commands.group()
    async def browse(self, ctx):
        """Browses reddit."""
        pass

    @browse.command()
    async def meme(self, ctx, category: str = None):
        """Get the hottest memes from a specific category.
        Available categories:
            - Anime
            - Minecraft
            - Dank
            - NGE
        """
        if (
            category is None
        ):  # if user doesn't provide a subreddit r/memes is the fallback subreddit
            submission = await self.get_submission(subreddit="memes", sorting="hot")
            e = Embed(ctx, title=f"Title: {submission.title}", image=submission.url)
            e.add_fields(
                (":thumbsup: **Upvotes**:", f"{submission.ups}"),
                (":envelepe: **Comments**:", f"{len(submission.comments)}"),
            )
            self.voting_message = await ctx.send(embed=e)

        else:  # use userprovided subreddit

            switcher = {  # why isn't there a built in switch function yet?
                "anime": "animemes",
                "dank": "dankmemes",
                "minecraft": "MinecraftMemes",
                "evangelion": "evangelionmemes",
                # TODO implement more subreddits
            }

            submission = await self.get_submission(
                subreddit=switcher.get(category), sorting="hot"
            )
            e = Embed(ctx, title=f"Title: {submission.title}", image=submission.url)
            e.add_fields(
                (":thumbsup: **Upvotes**:", f"{submission.ups}"),
                (":envelepe: **Comments**:", f"{len(submission.comments)}"),
            )
            self.voting_message = await ctx.send(embed=e)

    @browse.command()
    async def hot(self, ctx, subreddit: str):
        """Browse hot submissions in a subreddit."""
        submission = await self.get_submission(subreddit, sorting="hot")
        e = Embed(ctx, title=f"Title: {submission.title}", image=submission.url)
        e.add_fields(
            (":thumbsup: **Upvotes**:", f"{submission.ups}"),
            (":envelepe: **Comments**:", f"{len(submission.comments)}"),
        )
        self.voting_message = await ctx.send(embed=e)

    @browse.command()
    async def new(self, ctx, subreddit: str):
        """Browse new submissions in a subreddit."""
        submission = await self.get_submission(subreddit, sorting="new")
        e = Embed(ctx, title=f"Title: {submission.title}", image=submission.url)
        e.add_fields(
            (":thumbsup: **Upvotes**:", f"{submission.ups}"),
            (":envelepe: **Comments**:", f"{len(submission.comments)}"),
        )
        self.voting_message = await ctx.send(embed=e)

    @browse.command()
    async def top(self, ctx, subreddit: str):
        """Browse top submissions in a subreddit."""
        submission = await self.get_submission(subreddit, sorting="top")
        e = Embed(ctx, title=f"Title: {submission.title}", image=submission.url)
        e.add_fields(
            (":thumbsup: **Upvotes**:", f"{submission.ups}"),
            (":envelepe: **Comments**:", f"{len(submission.comments)}"),
        )
        self.voting_message = await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(RedditCog(bot))
