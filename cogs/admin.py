import discord
import importlib
import os
import logging

from discord.ext import commands
from .utils import checks

log = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    @checks.is_admin()
    @commands.command()
    async def load(self, ctx, name: str):
        """Loads an extension."""
        try:
            self.bot.load_extension(f'cogs.{name}')
        except Exception as e:
            log.error(f'{name} couldn\'t be loaded.\n{e}')
        await ctx.send(f'Loaded extension **{name}.py**')

    @checks.is_admin()
    @commands.command()
    async def unload(self, ctx, name: str):
        """Unloads an extension."""
        try:
            self.bot.unload_extension(f'cogs.{name}')
        except Exception as e:
            log.error(f'{name} couldn\'t be unloaded.\n{e}')
        await ctx.send(f'Unloaded extension **{name}.py**')

    @checks.is_admin()
    @commands.command()
    async def reload(self, ctx, name: str):
        """Reloads an extension."""
        try:
            self.bot.reload_extension(f'cogs.{name}')
        except Exception as e:
            log.error(f'{name} couldn\'t be reloaded.\n{e}')
        await ctx.send(f'Reloaded extension **{name}.py**')

    @checks.is_admin()
    @commands.command()
    async def reloadall(self, ctx):
        """Reloads all extensions."""
        error_collection = []
        for file in os.listdir('cogs'):
            if file.endswith('.py'):
                name = file[:-3]
                try:
                    self.bot.reload_extension(f'cogs.{name}')
                except Exception as e:
                    log.error(f'{name} couldn\'t be loaded.\n{e}')

        if error_collection:
            output = '\n'.join([f'**{g[0]}** ```diff\n- {g[1]}```' for g in error_collection])
            return await ctx.send(
                f'Attempted to reload all extensions, was able to reload, '
                f'however the following failed...\n\n{output}'
            )

        await ctx.send('Successfully reloaded all extensions')

    @checks.is_admin()
    @commands.command()
    async def reloadutils(self, ctx, name: str):
        """ Reloads a utils module. """
        name_maker = f'utils/{name}.py'
        try:
            module_name = importlib.import_module(f'utils.{name}')
            importlib.reload(module_name)
        except ModuleNotFoundError:
            return await ctx.send(f'Couldn\'t find module named **{name_maker}**')
        except Exception as e:
            return await ctx.send(f'Module **{name_maker}** returned error and was not reloaded...\n{e}')
        await ctx.send(f'Reloaded module **{name_maker}**')

    @checks.is_admin()
    @commands.command()
    async def dm(self, ctx, user_id: int, *, message: str):
        """ DM the user of your choice """
        user = self.bot.get_user(user_id)
        if not user:
            return await ctx.send(f'Could not find any UserID matching **{user_id}**')

        try:
            await user.send(message)
            await ctx.send(f'✉️ Sent a DM to **{user_id}**')
        except discord.Forbidden:
            await ctx.send('This user might be having DMs blocked or it\'s a bot account...')

    @checks.is_admin()
    @commands.command(name='status')
    async def change_playing(self, ctx, *, playing: str, status: str, playing_type: str):
        """ Change playing status. """
        def get_status(status):
            switcher = {
                'idle': discord.Status.idle,
                'dnd': discord.Status.dnd,
                'online': discord.Status.online
            }
            return switcher.get(status, 'Invalid status.')

        def get_playing(playing_type):
            switcher = {
                'playing': 0,
                'listening': 2,
                'watching': 3,
            }
            return switcher.get(playing_type, 'Invalid game.')

        try:
            await self.bot.change_presence(
                activity=discord.Activity(type=get_playing(playing_type), name=playing),
                status=get_status(status)
            )
            await ctx.send('\N{OK HAND SIGN}')
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)

    @checks.is_admin()
    @commands.command(name='username')
    async def change_username(self, ctx, *, name: str):
        """ Change username. """
        try:
            await self.bot.user.edit(username=name)
            await ctx.send('\N{OK HAND SIGN}')
        except discord.HTTPException as err:
            await ctx.send(err)

    @checks.is_admin()
    @commands.command(name='nickname')
    async def change_nickname(self, ctx, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                await ctx.send('\N{OK HAND SIGN}')
            else:
                await ctx.send('\N{OK HAND SIGN}')
        except Exception as err:
            await ctx.send(err)


def setup(bot):
    bot.add_cog(Admin(bot))
