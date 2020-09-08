import discord
import traceback
import sys
from discord.ext import commands
import logging


log = logging.getLogger("cogs.events")


class EventsCog(commands.Cog):
    """Custom events for Discord."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.bot.config.enable_msg_logging:
            if str(message.channel.id) in self.bot.config.msg_logging_channel:
                f = open("./data/msgs.txt", "a")
                f.write(f"{message.author.name}: {message.content}\n")
                f.close()
                log.info("Message logged")

    # TODO: all of that
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command."""
        pass


def setup(bot):
    bot.add_cog(EventsCog(bot))
