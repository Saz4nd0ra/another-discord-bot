from discord.ext import commands
from .utils import db
from .utils.formats import plural
from collections import defaultdict

import discord
import re


class Profiles(db.Table):
    # this is the user_id
    id = db.Column(db.Integer(big=True), primary_key=True)


class DisambiguateMember(commands.IDConverter):
    async def convert(self, ctx, argument):
        # check if it's a user ID or mention
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]+)>$', argument)

        if match is not None:
            # exact matches, like user ID + mention should search
            # for every member we can see rather than just this guild.
            user_id = int(match.group(1))
            result = ctx.bot.get_user(user_id)
            if result is None:
                raise commands.BadArgument("Could not find this member.")
            return result

        # check if we have a discriminator:
        if len(argument) > 5 and argument[-5] == '#':
            # note: the above is true for name#discrim as well
            name, _, discriminator = argument.rpartition('#')
            pred = lambda u: u.name == name and u.discriminator == discriminator
            result = discord.utils.find(pred, ctx.bot.users)
        else:
            # disambiguate I guess
            if ctx.guild is None:
                matches = [
                    user for user in ctx.bot.users
                    if user.name == argument
                ]
                entry = str
            else:
                matches = [
                    member for member in ctx.guild.members
                    if member.name == argument
                    or (member.nick and member.nick == argument)
                ]

                def to_str(m):
                    if m.nick:
                        return f'{m} (a.k.a {m.nick})'
                    else:
                        return str(m)

                entry = to_str

            try:
                result = await ctx.disambiguate(matches, entry)
            except Exception as e:
                raise commands.BadArgument(f'Could not find this member. {e}') from None

        if result is None:
            raise commands.BadArgument("Could not found this member. Note this is case sensitive.")
        return result

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    @commands.group(invoke_without_command=True)
    async def profile(self, ctx, *, member: DisambiguateMember = None):
        """Manages your profile.

        If you don't pass in a subcommand, it will do a lookup based on
        the member passed in. If no member is passed in, you will
        get your own profile.

        All commands will create a profile for you.
        """

        member = member or ctx.author

        query = """SELECT * FROM profiles WHERE id=$1;"""
        record = await ctx.db.fetchrow(query, member.id)

        if record is None:
            if member == ctx.author:
                await ctx.send('You did not set up a profile.' \
                              f' If you want to input a switch friend code, type {ctx.prefix}profile switch 1234-5678-9012' \
                              f' or check {ctx.prefix}help profile')
            else:
                await ctx.send('This member did not set up a profile.')
            return

        # 0xF02D7D - Splatoon 2 Pink
        # 0x19D719 - Splatoon 2 Green
        e = discord.Embed(color=discord.Color.blurple())

        for key, value in keys.items():
            e.add_field(name=value, value=record[key] or 'N/A', inline=True)

        e.set_author(name=member.display_name, icon_url=member.avatar_url_as(format='png'))

        await ctx.send(embed=e)

    async def edit_fields(self, ctx, **fields):
        keys = ', '.join(fields)
        values = ', '.join(f'${2 + i}' for i in range(len(fields)))

        query = f"""INSERT INTO profiles (id, {keys})
                    VALUES ($1, {values})
                    ON CONFLICT (id)
                    DO UPDATE
                    SET ({keys}) = ROW({values});
                 """

        await ctx.db.execute(query, ctx.author.id, *fields.values())

def setup(bot):
    bot.add_cog(Profile(bot))
