import discord
from discord.ext import commands

import logging
import datetime
import json
import aiohttp
from collections import Counter

from cogs.utils.config import Config
c = Config()

log = logging.getLogger(__name__)

description = """Put a description there for fucks sake."""

initial_extensions = {

    'cogs.general'

}


class ADB(commands.Bot): # using a normal bot, no shards or anything fancy
    def __init__(self):
        super().__init__(command_prefix=c.command_prefix, description=description)

        self.session = aiohttp.ClientSession(loop=self.loop)

        # TODO blacklist
        self.blacklist = None

        # load cogs
        for ext in initial_extensions:
            try:
                self.load_extension(ext)
                log.info('Loaded %s' % ext)
            except Exception as e:
                log.error('Couldn\'t load %s due to %s . . .' % (ext, e))

    # TODO logging system for spammers
    async def log_spammers(self):
        pass

    async def add_to_blacklist(self, object_id):
        await self.blacklist.put(object_id, True)

    async def remove_from_blacklist(self, object_id):
        try:
            await self.blacklist.remove(object_id)
        except KeyError:
            pass

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        if ctx.author.id in self.blacklist:
            return

        if ctx.guild is not None and ctx.guild.id in self.blacklist:
            return

        await self.invoke(ctx)

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    # starting function for the bot, the bot gets started from launcher.py

    # TODO make that stuff fancier, by allowing the user to change the token when an error occurs
    def run(self):
        try:
            print('Starting bot!')
            super().run(c.login_token, reconnect=True)
        except discord.LoginFailure:
            log.error('Login failed, check the token')