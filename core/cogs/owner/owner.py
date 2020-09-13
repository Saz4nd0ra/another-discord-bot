import discord
import logging
from discord.ext import commands
from ...utils import checks
from ...utils.context import Context
from ...utils.embed import Embed

log = logging.getLogger(__name__)


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
