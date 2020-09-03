import discord
import typing
from discord.ext import commands
from discord.ext.commands import Context
import asyncio
import datetime
import random

from typing import Tuple


class Embed(discord.Embed):
    def __init__(self, ctx: Context = None, *, title: str, **kwargs):
        super(Embed, self).__init__(**kwargs)
        self.ctx = ctx if ctx else None
        self.timestamp = ctx.message.created_at

        if ctx:
            author_image = self.ctx.author.avatar_url
            self.set_author(name=title, icon_url=author_image)

        # if kwargs have an argument called colour, set the embed to colour to that
        # else default to discord blurple

        self.colour = int(kwargs.get("colour")) if kwargs.get("colour") else 0x7289DA

        self.description = kwargs.get("description")

        self.set_footer(
            text="Saz4nd0ra/another-discord-bot",
            icon_url="https://i.imgur.com/gFHBoZA.png",
        )

        if kwargs.get("image"):
            self.set_image(url=kwargs.get("image"))
        if kwargs.get("thumbnail"):
            self.set_thumbnail(url=kwargs.get("thumbnail"))

    def add_fields(self, *fields: Tuple[str, str]):
        for name, value in fields:
            self.add_field(name=name, value=value)

    def add_field(self, *field: Tuple[str, str]):
        self.add_field(name=Tuple[0], value=Tuple[1])
