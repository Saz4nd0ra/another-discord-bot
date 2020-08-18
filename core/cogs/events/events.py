import discord
from discord.ext import commands
import logging
from ...utils import checks

log = logging.getLogger(__name__)

class Events(commands.Cog):
    """Custom events for Discord."""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.bot.config.enable_msg_logging:
            if str(message.channel.id) == self.bot.config.msg_logging_channel:
                f = open("./data/msgs.txt", "a")
                f.write(f'{message.author.name}: {message.content}\n')
                f.close()
                log.info('Message logged')

def setup(bot):
    bot.add_cog(Events(bot))