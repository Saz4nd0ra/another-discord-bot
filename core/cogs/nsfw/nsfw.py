import discord
import rule34
from ...utils import checks
import asyncio
import random
import io
from ...utils.exceptions import *
from ...utils.embed import Embed
from discord.ext import commands

VIDEO_FORMATS = [
    "mp4",
    "webm",
    # and so on, I don't really know which formats r34 uses
]


class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
        self.loop = asyncio.get_event_loop()
        self.rule34 = rule34.Rule34(self.loop)

    # TODO work on a blacklist system and user configs (yikes)
    @checks.is_nsfw_channel()
    @commands.command()
    async def r34(self, ctx, *, search):

        images = await self.rule34.getImages(tags=search)
        file = images[random.randint(0, len(images))]

        # TODO work on filtering videos, so we can actually send them
        if any(x in file.file_url for x in VIDEO_FORMATS):
            embed = Embed(ctx, title="Video found.")
            if file.source:
                embed.add_field(name="Source:", value=f"[Click Here!]({file.source})")
            await ctx.send(embed=embed)
            await ctx.send(file.file_url)
        else:
            embed = Embed(ctx, title="Image found.", image=images[random.randint(0, len(images))].file_url)
            if file.source:
                embed.add_field(name="Source:", value=f"[Click Here!]({file.source})")
            await ctx.send(embed=embed)

    @checks.is_nsfw_channel()
    @commands.command()
    async def danbooru(self, ctx, *, search):

        await ctx.send("Not working yet.")



def setup(bot):
    bot.add_cog(NSFW(bot))
