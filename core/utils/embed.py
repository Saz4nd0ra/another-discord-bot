import discord
import typing
from discord.ext import commands
from discord.ext.commands import Context
import asyncio
import datetime
import random

from typing import Tuple

# TODO all of that

# TODO check for kwargs


class Embed(discord.Embed):
    def __init__(self, ctx: Context = None, *, title: str, **kwargs):
        super(Embed, self).__init__(**kwargs)
        self.ctx = ctx if ctx else None
        self.timestamp = ctx.message.created_at

        if ctx:
            author_image = self.ctx.author.avatar_url
            self.set_author(name=title, icon_url=author_image)

        self.description = kwargs.get("description")

        if ctx:
            footer_image = self.ctx.bot.user.avatar_url
            self.set_footer(
                text="Saz4nd0ra/another-discord-bot", icon_url=footer_image
            )
        else:
            pass
        if kwargs.get("image"):
            self.set_image(url=kwargs.get("image"))
        if kwargs.get("thumbnail"):
            self.set_thumbnail(url=kwargs.get("thumbnail"))

    def add_fields(self, *fields: Tuple[str, str]):
        for name, value in fields:
            self.add_field(name=name, value=value, inline=True)