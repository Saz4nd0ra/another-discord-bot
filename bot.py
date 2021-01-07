from discord.ext import commands
import discord
from cogs.utils import context
from cogs.utils.help import HelpCommand
from cogs.utils.config import Config
import datetime
import json
import logging
import aiohttp
import traceback
import sys
from collections import deque, defaultdict

DESCRIPTION = """
another-discord-bot
"""

log = logging.getLogger(__name__)


initial_extensions = (
    "cogs.general",
    "cogs.mod",
    "cogs.music",
    "cogs.nsfw",
    "cogs.reddit",
)


class ADB(commands.AutoShardedBot):
    def __init__(self, config=Config()):
        super().__init__(
            command_prefix=config,
            description=DESCRIPTION,
            fetch_offline_members=False,
            heartbeat_timeout=150.0,
            help_command=HelpCommand(),
        )
        self.config = config
        self.session = aiohttp.ClientSession(loop=self.loop)

        self._prev_events = deque(maxlen=10)

        # shard_id: List[datetime.datetime]
        # shows the last attempted IDENTIFYs and RESUMEs
        self.resumes = defaultdict(list)
        self.identifies = defaultdict(list)

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f"Failed to load extension {extension}.", file=sys.stderr)
                traceback.print_exc()

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
        if self.config.enable_msg_logging:
            if message.channel.id in self.config.msg_logging_channel:
                f = open("./data/msgs.txt", "a")
                f.write(f"{message.author.name}: {message.content}\n")
                f.close()
                log.info("Message logged")

    async def close(self):
        await super().close()
        await self.session.close()

    def run(self):
        super().run(self.config.login_token, reconnect=True)
