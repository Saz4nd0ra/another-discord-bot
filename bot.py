import discord
from discord.ext import commands

import logging
import datetime
import json
import aiohttp

from cogs.utils.config import Config
c = Config()

log = logging.getLogger(__name__)

description = """Put a description there for fucks sake."""

token = 'NzA4MzU5MzI3MjczOTc1ODM5.XuuA7Q.1ZTv5Oslbdmb0eRVcJpz8RqWvFg'

initial_extensions = {

    'cogs.general'

}

class ADB(commands.Bot): # using a normal bot, no shards or anything fancy
    def __init__(self):
        super().__init__(command_prefix=c.command_prefix, description=description)

        self.session = aiohttp.ClientSession(loop=self.loop)

        # load cogs
        for ext in initial_extensions:
            try:
                self.load_extension(ext)
                log.info('Loaded %s' % ext)
            except Exception as e:
                log.error('Couldn\'t load %s due to %s . . .' % (ext, e))

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()

        print('Ready: %s (ID: %s)' % (self.user, self.user.id))

    # starting function for the bot, the bot gets started from launcher.py
    def run(self):
        try:
            print('Starting bot!')
            super().run(c.login_token, reconnect=True)
        except discord.LoginFailure:
            log.error('Login failed, check the token')