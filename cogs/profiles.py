from discord.ext import commands
from .utils import db
from .utils.formats import plural
from collections import defaultdict

import discord
import re


class Profiles(db.Table):
    # this is the user_id
    id = db.Column(db.Integer(big=True), primary_key=True)
    nnid = db.Column(db.String)
    squad = db.Column(db.String)

    # merger from the ?fc stuff
    fc_3ds = db.Column(db.String)
    fc_switch = db.Column(db.String)

    # extra Splatoon data is stored here
    extra = db.Column(db.JSON, default="'{}'::jsonb", nullable=False)


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

def valid_nnid(argument):
    arg = argument.strip('"')
    if len(arg) > 16:
        raise commands.BadArgument('An NNID has a maximum of 16 characters.')
    return arg

_rank = re.compile(r'^(?P<mode>\w+(?:\s*\w+)?)\s*(?P<rank>[AaBbCcSsXx][\+-]?)\s*(?P<number>[0-9]{0,4})$')

def valid_rank(argument, *, _rank=_rank):
    m = _rank.match(argument.strip('"'))
    if m is None:
        raise commands.BadArgument('Could not figure out mode or rank.')

    mode = m.group('mode')
    valid = {
        'zones': 'Splat Zones',
        'splat zones': 'Splat Zones',
        'sz': 'Splat Zones',
        'zone': 'Splat Zones',
        'splat': 'Splat Zones',
        'tower': 'Tower Control',
        'control': 'Tower Control',
        'tc': 'Tower Control',
        'tower control': 'Tower Control',
        'rain': 'Rainmaker',
        'rainmaker': 'Rainmaker',
        'rain maker': 'Rainmaker',
        'rm': 'Rainmaker',
        'clam blitz': 'Clam Blitz',
        'clam': 'Clam Blitz',
        'blitz': 'Clam Blitz',
        'cb': 'Clam Blitz',
    }

    try:
        mode = valid[mode.lower()]
    except KeyError:
        raise commands.BadArgument(f'Unknown Splatoon 2 mode: {mode}') from None

    rank = m.group('rank').upper()
    if rank == 'S-':
        rank = 'S'

    number = m.group('number')
    if number:
        number = int(number)

        if number and rank not in ('S+', 'X'):
            raise commands.BadArgument('Only S+ or X can input numbers.')
        if rank == 'S+' and number > 10:
            raise commands.BadArgument('S+10 is the current cap.')

    return mode, { 'rank': rank, 'number': number }

def valid_squad(argument):
    arg = argument.strip('"')
    if len(arg) > 100:
        raise commands.BadArgument('Squad name way too long. Keep it less than 100 characters.')

    if arg.startswith('http'):
        arg = f'<{arg}>'
    return arg

_friend_code = re.compile(r'^(?:(?:SW|3DS)[- _]?)?(?P<one>[0-9]{4})[- _]?(?P<two>[0-9]{4})[- _]?(?P<three>[0-9]{4})$')

def valid_fc(argument, *, _fc=_friend_code):
    fc = argument.upper().strip('"')
    m = _fc.match(fc)
    if m is None:
        raise commands.BadArgument('Not a valid friend code!')

    return '{one}-{two}-{three}'.format(**m.groupdict())

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
        e = discord.Embed(colour=0x19D719)

        keys = {
            'fc_switch': 'Switch FC',
            'nnid': 'Wii U NNID',
            'fc_3ds': '3DS FC'
        }

        for key, value in keys.items():
            e.add_field(name=value, value=record[key] or 'N/A', inline=True)

        # consoles = [f'__{v}__: {record[k]}' for k, v in keys.items() if record[k] is not None]
        # e.add_field(name='Consoles', value='\n'.join(consoles) if consoles else 'None!', inline=False)
        e.set_author(name=member.display_name, icon_url=member.avatar_url_as(format='png'))

        extra = record['extra'] or {}
        rank = extra.get('sp2_rank', {})
        value = 'Unranked'
        if rank:
            value = '\n'.join(f'{mode}: {data["rank"]}{data["number"]}' for mode, data in rank.items())

        e.add_field(name='Splatoon 2 Ranks', value=value)

        weapon = extra.get('sp2_weapon')
        e.add_field(name='Splatoon 2 Weapon', value=weapon and weapon['name'])

        e.add_field(name='Squad', value=record['squad'] or 'N/A')
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
