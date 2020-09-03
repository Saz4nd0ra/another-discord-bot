import discord
import traceback
import sys
from discord.ext import commands
import logging


log = logging.getLogger("cogs.events")


class Events(commands.Cog):
    """Custom events for Discord."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.bot.config.enable_msg_logging:
            if message.channel.id in self.bot.config.msg_logging_channel:
                f = open("./data/msgs.txt", "a")
                f.write(f"{message.author.name}: {message.content}\n")
                f.close()
                log.info("Message logged")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        Parameters"""
        if hasattr(ctx.command, "on_error"):
            return

        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound,)
        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.error(f"{ctx.command} has been disabled.")

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.embed(
                    f"{ctx.command} can not be used in Private Messages."
                )
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == "tag list":
                await ctx.error("I could not find that member. Please try again.")

        else:
            print(
                "Ignoring exception in command {}:".format(ctx.command), file=sys.stderr
            )
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )

    @commands.command(name="do", aliases=["mimic", "copy"])
    async def do_repeat(self, ctx, *, inp: str):
        """A simple command which repeats your input!
        Parameters"""
        await ctx.send(inp)

    @do_repeat.error
    async def do_repeat_handler(self, ctx, error):
        """A local Error Handler for our command do_repeat.
        This will only listen for errors in do_repeat.
        The global on_command_error will still be invoked after.
        """

        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == "inp":
                await ctx.error("You forgot to give me input to repeat!")


def setup(bot):
    bot.add_cog(Events(bot))
