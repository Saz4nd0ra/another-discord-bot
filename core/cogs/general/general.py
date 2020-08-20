import logging
import discord
from discord.ext import commands
from ...utils.embed import Embed
import random
import humanize

log = logging.getLogger(__name__)


class General(commands.Cog):
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

        e = Embed(ctx=ctx, title=f"User: {user.name}", thumbnail=user.avatar_url)

        if hasattr(user, "nick"):
            nick = user.nick
        else:
            nick = user.name

        e.add_fields(
            ("Username:", f"{user}"),
            ("Display name:", f"{user.nick}"),
            ("ID:", f"{user.id}"),
            ("Created:", f"{humanize.naturaldate(user.created_at)}"),
            ("Joined:", f"{humanize.naturaldate(user.joined_at)}"),
            ("Roles:", f"{show_roles}")
        )

        await ctx.send(embed=e)

    @commands.group()
    async def server(self, ctx):
        """Check info about current server"""
        if ctx.invoked_subcommand is None:
            findbots = sum(1 for member in ctx.guild.members if member.bot)

            if ctx.guild.icon:
                thumbnail = ctx.guild.icon_url
            if ctx.guild.banner:
                image = ctx.guild.banner_url_as(format="png")

            e = Embed(
                title=f"Server: {ctx.guild.name}", image=image, thumbnail=thumbnail
            )

            e.add_field(name="Server Name:", value=ctx.guild.name, inline=True)
            e.add_field(name="Server ID:", value=ctx.guild.id, inline=True)
            e.add_field(name="Members:", value=ctx.guild.member_count, inline=True)
            e.add_field(name="Bots:", value=str(findbots), inline=True)
            e.add_field(name="Owner:", value=ctx.guild.owner, inline=True)
            e.add_field(name="Region:", value=ctx.guild.region, inline=True)
            e.add_field(
                name="Created:",
                value=humanize.naturaldate(ctx.guild.created_at),
                inline=True,
            )
            await ctx.send(embed=e)

    @server.command()
    async def icon(self, ctx):
        """Get the current server icon"""
        if not ctx.guild.icon:
            return await ctx.send("This server does not have a avatar.")
        await ctx.send(ctx.guild.icon_url_as(size=512))

    @server.command()
    async def banner(self, ctx):
        """Get the current banner image"""
        if not ctx.guild.banner:
            return await ctx.send("This server does not have a banner.")
        await ctx.send(ctx.guild.banner_url_as(format="png"))

    @commands.command()
    async def choice(self, ctx, *options):
        """Chooses between multiple options"""
        if not len(options) > 0:
            await ctx.send("You gotta give me a couple different options.")
        else:
            await ctx.send(random.choice(options))

    @commands.command()
    async def number(self, ctx, maximum: int, minimum: int = 0):
        """Gives a random number"""
        result = None
        if maximum < minimum:
            result = random.randint(maximum, minimum)
        else:
            result = random.randint(minimum, maximum)
        await ctx.send(result)


def setup(bot):
    bot.add_cog(General(bot))
