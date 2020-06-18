import discord
from discord.ext import commands
import logging
from .utils import checks
from .utils.config import Config
c = Config()

log = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_admin
    @commands.command
    async def ban(self, ctx, user: discord.Member):
        pass

    @checks.is_admin
    @commands.command
    async def kick(self, ctx, user: discord.Member):
        pass


def setup(bot):
    bot.add_cog(Admin(bot))
