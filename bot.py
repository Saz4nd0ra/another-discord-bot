import discord
from discord.ext import commands

import logging
import datetime
import json
import aiohttp
from collections import Counter

from cogs.utils.json import JSON
from cogs.utils.config import Config
c = Config()

log = logging.getLogger(__name__)

description = """Put a description there for fucks sake."""

initial_extensions = {

    'cogs.general'

}


class ADB(commands.Bot):  # using a normal bot, no shards or anything fancy
    def __init__(self):
        super().__init__(command_prefix=c.command_prefix, description=description)

        self.session = aiohttp.ClientSession(loop=self.loop)

        self.blacklist = JSON('blacklist.json')

        # add cooldown mapping for people who excessively spam commands
        self.spam_control = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user)

        # a simple spam counter, when it reaches 5, the user gets banned
        self._auto_spam_count = Counter()

        # load cogs
        for ext in initial_extensions:
            try:
                self.load_extension(ext)
                log.info('Loaded %s' % ext)
            except Exception as e:
                log.error('Couldn\'t load %s due to %s . . .' % (ext, e))

    async def add_to_blacklist(self, object_id):
        await self.blacklist.put(object_id, True)

    async def remove_from_blacklist(self, object_id):
        try:
            await self.blacklist.remove(object_id)
        except KeyError:
            pass

    @property
    def stats_wh(self):
        # TODO implement wh_id and wh_token
        wh_id, wh_token = self.wh.stat_webhook
        hook = discord.Webhook.partial(id=wh_id, token=wh_token, adapter=discord.AsyncWebhookAdapter(self.session))
        return hook

    # TODO spam logger
    def log_spam(self, ctx, message):
        pass

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        if ctx.author.id in self.blacklist:
            return

        if ctx.guild is not None and ctx.guild.id in self.blacklist:
            return

        # TODO implement a spam log
        bucket = self.spam_control.get_bucket(message)
        current = message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()
        author_id = message.author.id

        if author_id != c.owner_id:
            self._auto_spam_count[author_id] += 1
            if self._auto_spam_count[author_id] >= 5:
                await self.add_to_blacklist(author_id)
                del self._auto_spam_count[author_id]
        else:
            self._auto_spam_count.pop(author_id, None)

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