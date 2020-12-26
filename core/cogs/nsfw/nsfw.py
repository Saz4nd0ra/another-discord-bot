import discord
from . import api
from .api import Sync, Rule34
from ...utils import checks
import asyncio
import random
from ...utils.exceptions import *
from ...utils.embed import Embed
from discord.ext import commands


class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
        self.l = asyncio.get_event_loop()
        self.rule34 = api.Rule34(self.l)


# TODO work on a blacklist system and user configs (yikes)
    @checks.is_nsfw_channel()
    @commands.command()
    async def r34(self, ctx, *, search):

        images = await self.rule34.getImages(tags=search)

        embed = Embed(ctx, title="Image found.", image=images[random.randint(0, len(images))].file_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(NSFW(bot))