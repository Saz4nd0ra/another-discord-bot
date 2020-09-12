import discord
from ...utils import context
from discord.utils import get
from discord.ext import commands, menus
from ...utils.embed import Embed
from ...utils.config import Config
import praw
from praw import Reddit
import copy
from praw import Reddit
import random

REDDIT_DOMAINS = [
    "reddit.com",
    "redd.it",
]  # need to find more domains, if there are any


# TODO : finish up and clean up api stuff
class API:
    def __init__(self):

        self.config = Config()
        self.connection = Reddit(
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

    async def get_submission_from_url(self, url: str):
        submission = self.connection.submission(url)
        return submission

    async def upvote_post(self, submission):
        pass

    async def downvote_post(self, submission):
        pass


# TODO fix all of that
class InteractiveMessage(menus.Menu):
    def __init__(self, *, embed, submission):
        super().__init__(timeout=60)

        self.submission = submission
        self.embed = embed

    def update_context(self, payload: discord.RawReactionActionEvent):

        ctx = copy.copy(self.ctx)
        ctx.author = payload.member

        return ctx

    def reaction_check(self, payload: discord.RawReactionActionEvent):
        if payload.event_type == "REACTION_REMOVE":
            return False

        if not payload.member:
            return False
        if payload.member.bot:
            return False
        if payload.message_id != self.message.id:
            return False

        return payload.emoji in self.buttons

    async def send_initial_message(self, ctx, channel: discord.TextChannel):
        return await channel.send(embed=self.embed)

# TODO implement method to undo a upvote

    @menus.button(emoji="\u2b06")
    async def upvote_command(self, payload: discord.RawReactionActionEvent, submission):
        """Upvote button"""
        ctx = self.update_context(payload)

        await API().upvote_post(submission=self.submission)

    @menus.button(emoji="\u2b06")
    async def downvote_command(self, payload: discord.RawReactionActionEvent):
        """Upvote button"""
        ctx = self.update_context(payload)

        await API().downvote_post(submission=self.submission)


class RedditCog(commands.Cog):
    """Browse reddit with those commands."""

    def __init__(self, bot):
        self.bot = bot
        self.api = API()
        self.config = self.bot.config
        self.voting_message = None

    async def build_embed(self, ctx, submission):
        """Embed that includes a voting system."""

        # napkin math
        downvotes = int(((submission.ups/(submission.upvote_ratio * 100)) * 100) - submission.ups)

        embed = Embed(ctx, title=f"{submission.title}", image=submission.url)
        embed.add_field(name="<:upvote:754073992771666020>", value=submission.ups)
        embed.add_field(name="<:downvote:754073959791722569>", value=downvotes)
        embed.add_fields(
            (":keyboard:", f"{len(submission.comments)}"),
            ("Vote ratio:", f"{int(submission.upvote_ratio * 100)}%"),
            ("Shortlink:", f"[Click Here!]({submission.shortlink})")
        )

        return embed

    @commands.Cog.listener()
    async def on_message(self, message):
        """Catch reddit links, check them, and then return them as a nice embed."""
        ctx = await self.bot.get_context(message, cls=context.Context)
        if any(x in message.content for x in REDDIT_DOMAINS):
            submission_url = message.content
            submission = await self.api.get_submission_from_url(submission_url)
            if submission.over_18 is True and message.channel.is_nsfw() is not True:
                await message.delete()
                await ctx.error(
                    f"{message.author.mention} this channel doesn't allow NSFW.", 10
                )
            else:
                embed = await self.build_embed(ctx, submission)
                await ctx.send(embed=embed)

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
            submission = await self.api.get_submission(subreddit="memes", sorting="hot")
            embed = await self.build_embed(ctx, submission)
            await ctx.send(embed=embed)

        else:  # use userprovided subreddit

            switcher = {  # why isn't there a built in switch function yet?
                "anime": "animemes",
                "dank": "dankmemes",
                "minecraft": "MinecraftMemes",
                "evangelion": "evangelionmemes",
                # TODO implement more subreddits
            }

            submission = await self.api.get_submission(
                switcher.get(category), "hot"
            )
            embed = await self.build_embed(ctx, submission)
            await ctx.send(embed=embed)

    @browse.command()
    async def hot(self, ctx, subreddit: str):
        """Browse hot submissions in a subreddit."""
        submission = await self.api.get_submission(subreddit, sorting="hot")
        embed = await self.build_embed(ctx, submission)
        await ctx.send(embed=embed)

    @browse.command()
    async def new(self, ctx, subreddit: str):
        """Browse new submissions in a subreddit."""
        submission = await self.api.get_submission(subreddit, sorting="new")
        embed = await self.build_embed(ctx, submission)
        await ctx.send(embed=embed)

    @browse.command()
    async def top(self, ctx, subreddit: str):
        """Browse top submissions in a subreddit."""
        submission = await self.api.get_submission(subreddit, sorting="top")
        embed = await self.build_embed(ctx, submission)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(RedditCog(bot))
