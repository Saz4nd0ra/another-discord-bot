import discord
from discord.ext import commands


class Formatting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _gen_embed(self):
        """Provides a basic template for embeds"""
        e = discord.Embed()
        e.colour = 7506394
        e.set_footer(text='Saz4nd0ra/another-discord-bot (%s)' % BOTVERSION, icon_url='https://i.imgur.com/gFHBoZA.png')
        e.set_author(name=self.bot.name, url='https://github.com/Just-Some-Bots/MusicBot', icon_url=self.bot.avatar_url)
        return e
