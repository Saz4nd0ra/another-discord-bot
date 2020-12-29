import discord
from ...utils import context
from discord.utils import get
from discord.ext import commands, menus
from ...utils.embed import Embed
from .api import API
from ...utils.config import Config
import copy

REDDIT_DOMAINS = [
    "reddit.com",
    "redd.it",
]  # need to find more domains, if there are any


class Reddit(commands.Cog):
    """Browse reddit with those commands."""

    def __init__(self, bot):
        self.bot = bot
        self.api = API()
        self.config = self.bot.config
        self.voting_message = None
        if self.config.enable_redditembed:
            self.enable_embed = True

    async def send_embed(self, ctx, submission):
        """Embed that doesn't include a voting system."""

        # napkin math
        downvotes = int(
            ((submission.ups / (submission.upvote_ratio * 100)) * 100) - submission.ups
        )

        VIDEO_URL = "v.redd.it"

        if VIDEO_URL in submission.url:
            image = "https://imgur.com/MKnguLq.png"
            has_video = True
        else:
            image = submission.url
            has_video = False

        embed = Embed(ctx, title=f"{submission.title}", image=image)

        embed.add_field(name="<:upvote:754073992771666020>", value=submission.ups)
        embed.add_field(name="<:downvote:754073959791722569>", value=downvotes)

        embed.add_fields(
            (":keyboard:", f"{len(submission.comments)}"),
            ("Vote ratio:", f"{int(submission.upvote_ratio * 100)}%"),
            ("Link:", f"[Click Here!]({submission.shortlink})"),
        )

        if has_video:
            await ctx.send(submission.url, embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Catch reddit links, check them, and then return them as a nice embed."""
        ctx = await self.bot.get_context(message, cls=context.Context)
        if self.enable_embed:
            if any(x in message.content for x in REDDIT_DOMAINS):
                reddit_url = message.content
                submission = await self.api.get_submission_from_url(reddit_url)
                if submission.over_18 and not message.channel.is_nsfw():
                    await message.delete()
                    await ctx.error(
                        f"{message.author.mention} this channel doesn't allow NSFW.", 10
                    )
                else:
                    await message.delete()
                    await self.send_embed(ctx, submission)

    @commands.command()
    async def meme(self, ctx, category: str = None):
        """Get the hottest memes from a specific category.
        Available categories:
            - Anime
            - Minecraft
            - Dank
            - NGE
        """
        if (
            category == None
        ):  # if user doesn't provide a subreddit r/memes is the fallback subreddit
            submission = await self.api.get_submission(subreddit="memes", sorting="hot")
            await self.send_embed(ctx, submission)

        else:  # use userprovided subreddit

            switcher = {  # why isn't there a built in switch function yet?
                "anime": "animemes",
                "dank": "dankmemes",
                "minecraft": "MinecraftMemes",
                "evangelion": "evangelionmemes",
                # TODO implement more subreddits
            }

            submission = await self.api.get_submission(switcher.get(category), "hot")
            await self.send_embed(ctx, submission)

    @commands.command()
    async def hot(self, ctx, subreddit: str):
        """Browse hot submissions in a subreddit."""
        submission = await self.api.get_submission(subreddit, sorting="hot")
        await self.send_embed(ctx, submission)

    @commands.command()
    async def new(self, ctx, subreddit: str):
        """Browse new submissions in a subreddit."""
        submission = await self.api.get_submission(subreddit, sorting="new")
        await self.send_embed(ctx, submission)

    @commands.command()
    async def top(self, ctx, subreddit: str):
        """Browse top submissions in a subreddit."""
        submission = await self.api.get_submission(subreddit, sorting="top")
        await self.send_embed(ctx, submission)


def setup(bot):
    bot.add_cog(Reddit(bot))
