from .utils.context import Context
from discord.ext import commands
from .utils.embed import Embed
from .utils.api import RedditAPI

REDDIT_DOMAINS = [
    "reddit.com",
    "redd.it",
]  # need to find more domains, if there are any


class Reddit(commands.Cog):
    """Browse reddit. There isn't really a lot to it."""

    def __init__(self, bot):
        self.bot = bot
        self.api = RedditAPI()
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
            if hasattr(submission, "preview"):
                preview_image_link = submission.preview["images"][0]["source"]["url"]
                embed = Embed(ctx, title=submission.title, thumbnail=preview_image_link)
            else:
                preview_image_link = "https://imgur.com/MKnguLq.png"
            embed = Embed(ctx, title=submission.title, thumbnail=preview_image_link)
        else:
            embed = Embed(ctx, title=submission.title, image=submission.url)

        embed.add_field(name="<:upvote:754073992771666020>", value=submission.ups)
        embed.add_field(name="<:downvote:754073959791722569>", value=downvotes)

        embed.add_fields(
            (":keyboard:", f"{len(submission.comments)}"),
            ("Vote ratio:", f"{int(submission.upvote_ratio * 100)}%"),
            ("Link:", f"[Click Here!]({submission.shortlink})"),
        )

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Catch reddit links, check them, and then return them as a nice embed."""
        ctx = await self.bot.get_context(message, cls=Context)
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
        """Get memes from a specific category.
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
            await self.send_embed(ctx, submission)

        else:  # use userprovided subreddit

            switcher = {  # why isn't there a built in switch function yet?
                "anime": "animemes",
                "dank": "dankmemes",
                "minecraft": "MinecraftMemes",
                "nge": "evangelionmemes",
                # TODO implement more subreddits
            }

            submission = await self.api.get_submission(
                switcher.get(category.lower()), "hot"
            )
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
