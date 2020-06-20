import discord
from discord.ext import commands
from discord import Webhook, RequestsWebhookAdapter

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
        hook = discord.Webhook.partial(id=c.wh_id, token=c.wh_token, adapter=discord.AsyncWebhookAdapter(self.session))
        return hook

    def log_spammer(self, ctx, message, retry_after, *, autoblock=False):
        guild_name = getattr(ctx.guild, 'name', 'No Guild (DMs)')
        guild_id = getattr(ctx.guild, 'id', None)
        fmt = 'User %s (ID %s) in guild %s (ID %s) spamming, retry_after: %.2fs'
        log.warning(fmt, message.author, message.author.id, guild_name, guild_id, retry_after)
        if not autoblock:
            return

        wh = self.stats_wh
        embed = discord.Embed(title='Auto-blocked Member', colour=0xDDA453)
        embed.add_field(name='Member:', value='%s (ID: %s)' % (message.author, message.author.id), inline=False)
        embed.add_field(name='Guild Info:', value='%s (ID: %s)' % (guild_name, guild_id), inline=False)
        embed.add_field(name='Channel Info:', value='%s (ID: %s)' % (message.channel, message.channel.id), inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        return wh.send(embed=embed)

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        if ctx.author.id in self.blacklist:
            return

        if ctx.guild is not None and ctx.guild.id in self.blacklist:
            return

        bucket = self.spam_control.get_bucket(message)
        current = message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()
        retry_after = bucket.update_rate_limit(current)
        author_id = message.author.id
        if retry_after and author_id != self.owner_id:
            self._auto_spam_count[author_id] += 1
            if self._auto_spam_count[author_id] >= 5:
                await self.add_to_blacklist(author_id)
                del self._auto_spam_count[author_id]
                await self.log_spammer(ctx, message, retry_after, autoblock=True)
            else:
                self.log_spammer(ctx, message, retry_after)
            return
        else:
            self._auto_spam_count.pop(author_id, None)

        await self.invoke(ctx)

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()

        print(f'Ready: %s (ID: %s)' % (self.user, self.user.id))

    # starting function for the bot, the bot gets started from launcher.py

    # TODO make that stuff fancier, by allowing the user to change the token when an error occurs
    def run(self):
        try:
            print('Starting bot!')
            super().run(c.login_token, reconnect=True)
        except discord.LoginFailure:
            log.error('Login failed, check the token')