import discord
import typing
from discord.ext import commands
import asyncio
import datetime
import random


class Embed(discord.Embed): # 
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        asyncio.create_task(self.__ainit__(**kwargs))

    async def __ainit__(self, **kwargs):
        self._colour = discord.Colour.from_hsv(random.random(), 1, 1)
        message = kwargs.get("message")
        title = kwargs.get("title")
        if title:
            kwargs.pop("title")

        if title:
            avatar_url = message.author.avatar_url_as(format="png") if message else None
            self.set_author(name=title, icon_url=avatar_url)

        self.set_footer(icon_url='https://i.imgur.com/gFHBoZA.png', text='github.com/Saz4nd0ra/another-discord-bot')

        self._timestamp = datetime.datetime.utcnow()