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
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send("This command cannot be used in private messages.")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send("Sorry. This command is disabled and cannot be used.")
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                print(f"In {ctx.command.qualified_name}:", file=sys.stderr)
                traceback.print_tb(original.__traceback__)
                print(f"{original.__class__.__name__}: {original}")
                await ctx.error(
                    "`Something went wrong when invoking the command. Check the logs.`"
                )
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.embed(error)


def setup(bot):
    bot.add_cog(EventsCog(bot))
