from discord.ext import commands
import discord
from .utils import context
from .utils.config import Config
import datetime
import json
import logging
import traceback
import sys
import aiohttp
from collections import Counter, deque, defaultdict

CONFIG = Config()

DESCRIPTION = """
another-discord-bot (dev branch)
"""

log = logging.getLogger(__name__)

cogs_to_load = {  # of course nothing works as planned
    "music",
    "reddit",
    "events",
    "general",
}


class ADB(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=CONFIG.prefix,
            description=DESCRIPTION,
            fetch_offline_members=False,
            heartbeat_timeout=150.0
        )

        self.session = aiohttp.ClientSession(loop=self.loop)

        self.config = CONFIG

        self._prev_events = deque(maxlen=10)

        # need to rework blacklist, already prepared a setting in config for ids to ignore, gonna elaborate more on it
        self.blacklist = None

        # shard_id: List[datetime.datetime]
        # shows the last attempted IDENTIFYs and RESUMEs
        self.resumes = defaultdict(list)
        self.identifies = defaultdict(list)

        for cog in cogs_to_load:
            try:
                cog_path = f"core.cogs.{cog}.{cog}"
                self.load_extension(cog_path)
                log.info(f"Loaded {cog}")
            except Exception as e:
                log.error(f"Failed to load extension {cog} due to {e}.")
                traceback.print_exc()

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send("This command cannot be used in private messages.")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send("Sorry. This command is disabled and cannot be used.")
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                print(f"In {ctx.command.qualified_name}:", file=sys.stderr)
                traceback.print_tb(original.__traceback__)
                print(f"{original.__class__.__name__}: {original}", file=sys.stderr)
                await ctx.send(
                    "`An error occurred while processing your command. Check the logs.`"
                )

    async def on_ready(self):  # maybe I should do it even fancier
        if not hasattr(self, "uptime"):
            self.uptime = datetime.datetime.utcnow()

        print(f"Ready: {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Streaming(
                name=f"{self.config.prefix}help",
                url="https://www.twitch.tv/commanderroot",
            )
        )

    async def on_shard_resumed(self, shard_id):
        print(f"Shard ID {shard_id} has resumed..")
        self.resumes[shard_id].append(datetime.datetime.utcnow())

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        if str(message.author.id) in str(self.config.blacklisted_ids):
            return

        await self.invoke(ctx)

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    async def close(self):
        await super().close()
        await self.session.close()

    def run(self):
        try:
            super().run(self.config.login_token, reconnect=True)
        finally:
            with open("logs/prev_events.log", "w", encoding="utf-8") as fp:
                for data in self._prev_events:
                    try:
                        x = json.dumps(data, ensure_ascii=True, indent=4)
                    except:
                        fp.write(f"{data}\n")
                    else:
                        fp.write(f"{x}\n")
