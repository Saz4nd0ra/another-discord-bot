import logging
import discord
from discord.ext import commands
from ...utils.embed import Embed
import random
import humanize
import unicodedata
import inspect
import os

log = logging.getLogger("cogs.general")


class GeneralCog(commands.Cog):
    """General commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def user(self, ctx, *, user: discord.Member = None):
        """Get user information"""
        user = user or ctx.author

        show_roles = (
            ", ".join(
                [
                    "<@&%s>" % x.id
                    for x in sorted(user.roles, key=lambda x: x.position, reverse=True)
                    if x.id != ctx.guild.default_role.id
                ]
            )
            if len(user.roles) > 1
            else "None"
        )

        e = Embed(ctx, title=f"User: {user.name}", thumbnail=user.avatar_url)

        if hasattr(user, "nick"):
            nick = user.nick
        else:
            nick = user.name

        e.add_fields(
            ("Username:", f"{user}"),
            ("Nickname:", f"{user.nick}"),
            ("ID:", f"{user.id}"),
            ("Created:", f"{humanize.naturaldate(user.created_at)}"),
            ("Joined:", f"{humanize.naturaldate(user.joined_at)}"),
            ("Roles:", f"{show_roles}"),
        )

        await ctx.send(embed=e)

    @commands.group()
    async def server(self, ctx):
        """Check info about current server"""
        if ctx.invoked_subcommand == None:
            findbots = sum(1 for member in ctx.guild.members if member.bot)

            if ctx.guild.icon:
                thumbnail = ctx.guild.icon_url
            if ctx.guild.banner:
                image = ctx.guild.banner_url_as(format="png")

            e = Embed(ctx, title=f"Server: {ctx.guild.name}", thumbnail=thumbnail)
            e.add_fields(
                ("Server ID:", f"{ctx.guild.id}"),
                ("Members:", f"{ctx.guild.member_count}"),
                ("Bots:", f"{str(findbots)}"),
                ("Owner:", f"{ctx.guild.owner}"),
                ("Region:", f"{ctx.guild.region}"),
                ("Created:", f"{humanize.naturaldate(ctx.guild.created_at)}"),
            )
            await ctx.send(embed=e)

    @server.command()
    async def icon(self, ctx):
        """Get the current server icon"""
        if not ctx.guild.icon:
            return await ctx.error("This server does not have a avatar.")
        e = Embed(
            ctx,
            title=f"{ctx.guild.name}s Server Icon",
            image=ctx.guild.icon_url_as(size=512),
        )
        await ctx.send(embed=e)

    @server.command()
    async def banner(self, ctx):
        """Get the current banner image"""
        if not ctx.guild.banner:
            return await ctx.error("This server does not have a banner.")
        e = Embed(
            ctx,
            title=f"{ctx.guild.name}s Server Banner",
            image=ctx.guild.icon_url_as(size=512),
        )
        await ctx.send(embed=e)

    @commands.command()
    async def charinfo(self, ctx, *, characters: str):
        """Shows you information about a number of characters.
        Only up to 25 characters at a time."""

        def to_string(c):
            digit = f"{ord(c):x}"
            name = unicodedata.name(c, "Name not found.")
            return f"`\\U{digit:>08}`: {name} - {c} \N{EM DASH} <http://www.fileformat.info/info/unicode/char/{digit}>"

        msg = "\n".join(map(to_string, characters))
        if len(msg) > 2000:
            return await ctx.send("Output too long to display.")
        await ctx.send(msg)

    @commands.command()
    async def source(self, ctx, *, command: str = None):
        """Displays my full source code or for a specific command."""
        source_url = "https://github.com/Saz4nd0ra/another-discord-bot"
        branch = "master"
        if command == None:
            return await ctx.send(source_url)

        if command == "help":
            src = type(self.bot.help_command)
            module = src.__module__
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command.replace(".", " "))
            if obj == None:
                return await ctx.error("Could not find command.")

            # since we found the command we're looking for, presumably anyway, let's
            # try to access the code itself
            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        location = os.path.relpath(filename).replace("\\", "/")

        final_url = f"<{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>"
        await ctx.send(final_url)

    @commands.group()
    async def random(self, ctx):
        """A group of commands to provide pseudo randomness."""

    @random.command()
    async def choice(self, ctx, *options):
        """Chooses between multiple options"""
        if not len(options) > 0:
            await ctx.error("You will have to give me a couple different options.")
        else:
            await ctx.send(f"**{random.choice(options)}**")

    @random.command()
    async def number(self, ctx, maximum: int, minimum: int = 0):
        """Gives a random number"""
        result = None
        if maximum < minimum:
            result = random.randint(maximum, minimum)
        else:
            result = random.randint(minimum, maximum)
        await ctx.send(result)


def setup(bot):
    bot.add_cog(GeneralCog(bot))
