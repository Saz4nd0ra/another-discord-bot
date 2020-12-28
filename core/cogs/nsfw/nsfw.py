import discord
from .api import Rule34API
from .api import DanbooruAPI
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
        self.rule34 = Rule34API()
        self.danbooru = DanbooruAPI()

    # TODO work on a blacklist system and user configs (yikes)
    @checks.is_nsfw_channel()
    @commands.command()
    async def r34(self, ctx, *, search):

        file, is_video, has_source = await self.rule34.get_random_r34(search)
        # TODO work on filtering videos, so we can actually send them
        if is_video:
            embed = Embed(ctx, title="Video found.", thumbnail=file.preview_url)
        else:
            embed = Embed(ctx, title="Image found.", image=file.file_url)
        if has_source:
            embed.add_field(name="Source:", value=f"[Click Here!]({file.source})")
        embed.add_field(name="Image/Video:", value=f"[Click Here!]({file.file_url})")

        await ctx.send(embed=embed)

    @checks.is_nsfw_channel()
    @commands.command()
    async def danbooru(self, ctx, *, search):

        file, is_video, has_source = self.danbooru.get_random_danbooru(search)

        file_source = file["source"]
        file_preview = file["preview_file_url"]
        file_url = file["file_url"]
        # TODO work on filtering videos, so we can actually send them
        if is_video:
            embed = Embed(ctx, title="Video found.", thumbnail=file_preview)
        else:
            embed = Embed(ctx, title="Image found.", image=file_url)
        if has_source:
            embed.add_field(name="Source:", value=f"[Click Here!]({file_source})")
        embed.add_field(name="Image/Video:", value=f"[Click Here!]({file_url})")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(NSFW(bot))
