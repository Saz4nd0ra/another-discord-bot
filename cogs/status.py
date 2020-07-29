import discord
from discord.ext import commands, tasks


class StatusCycler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_dict = {
            'status': [
                {'name': f'@ me or use !help'},
                {'name': ''},
                {'name': '', 'type': 1},
            ]
        }
        self.status_cycler.start()
        self.status_counter = 0

    def cog_unload(self):
        self.status_cycler.cancel()

    @tasks.loop(minutes=10.0)
    async def status_cycler(self):
        status = self.status_dict['status'][self.status_counter]
        await self.bot.change_presence(
            activity=discord.Streaming(name=status['name'], url='https://www.twitch.tv/commanderroot')
        )
        self.status_counter += 1
        if self.status_counter == len(self.status_dict['status']):
            self.status_counter = 0

    @status_cycler.before_loop
    async def before_status_cycler(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(StatusCycler(bot))