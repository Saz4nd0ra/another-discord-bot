import discord
import typing
from discord.ext import commands
import asyncio
import datetime


class Embed(discord.Embed):
    def __init__(self, bot, message: typing.Union[commands.Context, discord.Message] = None, **kwargs):
        super().__init__(**kwargs)
        asyncio.create_task(self.__ainit__(bot, message, **kwargs))

    async def __ainit__(self, bot, message, **kwargs):
        self._color = discord.Color.blurple()
        if isinstance(message, commands.Context):
            message = message.message
        title = kwargs.get("title")
        if title:
            kwargs.pop("title")

        if title:
            avatar_url = message.author.avatar_url_as(format="png") if message else None
            self.set_author(name=title, icon_url=avatar_url)

        icon_url = bot.user.avatar_url_as(format="png")
        self.set_footer(icon_url='https://i.imgur.com/gFHBoZA.png', text='Saz4nd0ra/another-discord-bot')


# Usage:
# from .utils.embed import
#
#
# embed = Embed(self.ctx.bot, self.ctx, description=foo, title=f'foor {bar}')
#
#

class SimpleEmbed(discord.Embed):
    def __init__(self, message: typing.Union[commands.Context, discord.Message] = None, **kwargs):
        super().__init__(**kwargs)
        asyncio.create_task(self.__ainit__(message, **kwargs))

    async def __ainit__(self, message, **kwargs):
        self._color = discord.Color.blurple()
        if isinstance(message, commands.Context):
            message = message.message
        title = kwargs.get("title")
        if title:
            kwargs.pop("title")

        if title:
            avatar_url = message.author.avatar_url_as(format="png") if message else None
            self.set_author(name=title, icon_url=avatar_url)
            
        self.set_footer(icon_url='https://i.imgur.com/gFHBoZA.png', text='Saz4nd0ra/another-discord-bot')