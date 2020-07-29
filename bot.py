from collections import Counter, deque
import logging
import datetime
import aiohttp
import discord
import traceback
import sys
from discord.ext import commands
from discord import Webhook
from cogs.utils import help, context

from cogs.utils.json import JSON
from cogs.utils.config import Config
config = Config()

log = logging.getLogger(__name__)

description = """"""

initial_extensions = (

    'cogs.general',
    'cogs.mod',
    'cogs.music',
    'cogs.admin',

)


class ADB(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or(config.command_prefix),
                         description=description,
                         help_command=help.HelpCommand())

        self.session = aiohttp.ClientSession(loop=self.loop)

        self._prev_events = deque(maxlen=10)
        self.config = Config()

        self.blacklist = JSON('blacklist.json')

        # add cooldown mapping for people who excessively spam commands
        self.spam_control = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user)

        # a simple spam counter, when it reaches 5, the user gets banned
        self._auto_spam_count = Counter()

        # load cogs
        for ext in initial_extensions:
            try:
                self.load_extension(ext)
                log.info(f'Loaded {ext}')
            except Exception as e:
                log.error(f'Couldn\'t load {ext} due to {e} . . .')
                log.error(traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr))

        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()

    async def get_context(self, message: discord.Message, *, cls=context.Context):
        return await super().get_context(message, cls=cls)

    async def add_to_blacklist(self, object_id):
        await self.blacklist.put(object_id, True)

    async def remove_from_blacklist(self, object_id):
        try:
            await self.blacklist.remove(object_id)
        except KeyError:
            pass

    @property
    def stats_wh(self):
        hook = Webhook.partial(id=config.wh_id, token=config.wh_token, adapter=discord.AsyncWebhookAdapter(self.session))
        return hook

    def log_spammer(self, ctx, message, retry_after, *, autoblock=False):
        guild_name = getattr(ctx.guild, 'name', 'No Guild (DMs)')
        guild_id = getattr(ctx.guild, 'id', None)
        fmt = 'User %s (ID %s) in guild %r (ID %s) spamming, retry_after: %.2fs'
        log.warning(fmt, message.author, message.author.id, guild_name, guild_id, retry_after)
        if not autoblock:
            return

        wh = self.stats_wh
        embed = discord.Embed(title='Auto-blocked Member', color=discord.Color.blurple())
        embed.add_field(name='Member', value=f'{message.author} (ID: {message.author.id})', inline=False)
        embed.add_field(name='Guild Info', value=f'{guild_name} (ID: {guild_id})', inline=False)
        embed.add_field(name='Channel Info', value=f'{message.channel} (ID: {message.channel.id}', inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        return wh.send(embed=embed)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                print(f'In {ctx.command.qualified_name}:', file=sys.stderr)
                traceback.print_tb(original.__traceback__)
                print(f'{original.__class__.__name__}: {original}', file=sys.stderr)
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(error)

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
        print(f'Ready: {self.user} (ID: {self.user.id})')
        await self.change_presence(
            activity=discord.Streaming(name=f'@ me or use {self.config.command_prefix}help',
                                       url='https://www.twitch.tv/commanderroot'))

    async def close(self):
        await super().close()
        await self.session.close()

    # starting function for the bot, the bot gets started from launcher.py

    # TODO make that stuff fancier, by allowing the user to change the token when an error occurs
    def run(self):
        try:
            super().run(config.login_token, reconnect=True)
        finally:
            with open('logs/prev_events.log', 'w', encoding='utf-8') as fp:
                for data in self._prev_events:
                    try:
                        x = json.dumps(data, ensure_ascii=True, indent=4)
                    except:
                        fp.write(f'{data}\n')
                    else:
                        fp.write(f'{x}\n')
