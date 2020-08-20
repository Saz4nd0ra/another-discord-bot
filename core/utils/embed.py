import discord
import typing
from discord.ext import commands
import asyncio
import datetime
import random

# TODO all of that

# TODO check for kwargs

class Embed(discord.Embed):
    def __init__(self, ctx: discord.ext.commands.context=None, message: discord.Message=None, **kwargs):
        """Accepted arguments: title, description, colour, image, thumbnail"""
        self.ctx = ctx if ctx else None
        self.message = message if message else None
        title = kwargs.get("title")
        kwargs.pop("title")
        if title and message:
            author_image = self.message.author.avatar_url
            self.set_author(name=title, icon_url=author_image)
        else:
            self.title = title

        self.description = kwargs.get("description")
        kwargs.pop("description")
        colour = kwargs.get("colour")
        if colour:
            self.colour = colour
        else:
            self.colour = discord.Colour.blurple()
            kwargs.pop("colour")

        footer_image = self.ctx.bot.user.avatar_url
        self.set_footer(text='github.com/Saz4nd0ra/another-discord-bot', icon_url=footer_image)
        if kwargs.get("image"):
            self.set_image(url=kwargs.get("image"))
            kwargs.pop("image")
        if kwargs.get("thumbnail"):
            self.set_thumbnail(url=kwargs.get("thumbnail"))
            kwargs.pop("thumbnail")
