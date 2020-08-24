import discord
import lavalink
from discord.ext import commands, menus
from ...utils import checks, embed

url_rx = re.compile(r'https?://(?:www\.)?.+')

class Music(commands.Cog):
    """Listen to music with."""

    def __init__(self, bot,):
        self.bot = bot
        self.config = self.bot.config

        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(self.config.ll_host,
                                  self.config.ll_port,
                                  self.config.ll_passwd,
                                  'eu',
                                  'default-node')

            bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')

    def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx): # this basically replaces the private messages check altogether, saving us lines of in addition
        guild_check = ctx.guild is not None

        if guild_check:
            try:
                await self.ensure_voice(ctx)
                
        return guild_check