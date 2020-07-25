import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')

    @commands.command()
    async def help(self, ctx):
        """Shows this message."""

def setup(bot):
    bot.add_cog(Help(bot))
