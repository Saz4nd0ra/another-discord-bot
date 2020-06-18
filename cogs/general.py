import logging
import discord
from discord.ext import commands
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

        show_roles = ', '.join(
            ['<@&%s>' % x.id for x in sorted(user.roles,
                                             key=lambda x: x.position,
                                             reverse=True)
                if x.id != ctx.guild.default_role.id]
        ) if len(user.roles) > 1 else 'None'

        embed = discord.Embed(colour=user.top_role.colour.value)
        embed.set_thumbnail(url=user.avatar_url)

        embed.add_field(name='Username:', value=user, inline=True)
        embed.add_field(name='Display name:',
                        value=user.nick if hasattr(user, 'nick') else 'None',
                        inline=True)
        embed.add_field(name='ID:', value=user.id, inline=False)
        embed.add_field(name='Created:',
                        value=humanize.naturaldate(user.created_at),
                        inline=True)
        embed.add_field(name='Joined:',
                        value=humanize.naturaldate(user.joined_at),
                        inline=True)

        embed.add_field(
            name='Roles',
            value=show_roles,
            inline=False
        )

        await ctx.send(content='ℹ About **%s**' % user.id, embed=embed)

    @commands.group()
    async def server(self, ctx):
        """Check info about current server"""
        if ctx.invoked_subcommand is None:
            findbots = sum(1 for member in ctx.guild.members if member.bot)

            embed = discord.Embed()

            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon_url)
            if ctx.guild.banner:
                embed.set_image(url=ctx.guild.banner_url_as(format='png'))

            embed.add_field(name='Server Name:',
                            value=ctx.guild.name, inline=True)
            embed.add_field(name='Server ID:',
                            value=ctx.guild.id, inline=True)
            embed.add_field(name='Members:',
                            value=ctx.guild.member_count, inline=True)
            embed.add_field(name='Bots:',
                            value=findbots, inline=True)
            embed.add_field(name='Owner:',
                            value=ctx.guild.owner, inline=True)
            embed.add_field(name='Region:',
                            value=ctx.guild.region, inline=True)
            embed.add_field(name='Created:',
                            value=humanize.naturaldate(ctx.guild.created_at),
                            inline=True)
            await ctx.send(content='ℹ information about **%s**' %
                           ctx.guild.name, embed=embed)

    @server.command(name='icon')
    async def server_icon(self, ctx):
        """Get the current server icon"""
        if not ctx.guild.icon:
            return await ctx.send('This server does not have a avatar.')
        await ctx.send(ctx.guild.icon_url_as(size=512))

    @server.command(name='banner')
    async def server_banner(self, ctx):
        """Get the current banner image"""
        if not ctx.guild.banner:
            return await ctx.send('This server does not have a banner.')
        await ctx.send(ctx.guild.banner_url_as(format='png'))

    @commands.command()
    async def choice(self, ctx, *options):
        """Chooses between multiple options"""
        if not len(options) > 0:
            await ctx.send('You gotta give me a couple different options.')
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
