import discord
from .api import Rule34
from ...utils import checks
import asyncio
import random
import pybooru as danbooru
from ...utils.exceptions import *
from ...utils.embed import Embed
from discord.ext import commands


class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
        self.rule34 = Rule34()

    # TODO work on a blacklist system and user configs (yikes)
    @checks.is_nsfw_channel()
    @commands.command()
    async def r34(self, ctx, *, search):

        file, is_video, has_source = await self.rule34.get_random_post_url(search)
        # TODO work on filtering videos, so we can actually send them
        if is_video:
            embed = Embed(ctx, title="Video found.", image=file.preview_url)
        else:
            embed = Embed(ctx, title="Image found.", image=file.preview_url)
        if has_source:
            embed.add_field(name="Source:", value=f"[Click Here!]({file.source})")
        embed.add_field(name="Image/Video:", value=f"[Click Here!]({file.file_url})")

        await ctx.send(embed=embed)

    @checks.is_nsfw_channel()
    @commands.command()
    async def danbooru(self, ctx, *, search):

        await ctx.send("Not working yet.")


def setup(bot):
    bot.add_cog(NSFW(bot))
