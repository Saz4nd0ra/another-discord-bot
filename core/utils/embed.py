import discord
import typing
from discord.ext import commands
import asyncio
import datetime
import random

# TODO all of that

class Embed:
    def __init__(self, ctx: discord.ext.commands.context, message: discord.Message, **kwargs):
        self.title = kwargs.get("title")
        self.description = kwargs.get("description")
        self.ctx = ctx
        self.message = message
