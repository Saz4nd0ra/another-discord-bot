# TODO make use of new message util to simplify embeds

import discord
from discord.ext import commands
import logging
from .utils import checks
from .utils.formats import Plural
from collections import Counter
from .utils.config import Config
c = Config()

log = logging.getLogger(__name__)


# converters and helpers
def can_execute_action(ctx, user, target):
    return user.id == ctx.bot.owner_id or \
           user == ctx.guild.owner or \
           user.top_role > target.top_role


class MemberNotFound(Exception):
    pass


async def resolve_member(guild, member_id):
    member = guild.get_member(member_id)
    if member is None:
        if guild.chunked:
            raise MemberNotFound()
        try:
            member = await guild.fetch_member(member_id)
        except discord.NotFound:
            raise MemberNotFound() from None
    return member


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                member_id = int(argument, base=10)
                m = await resolve_member(ctx.guild, member_id)
            except ValueError:
                raise commands.BadArgument('%s is not a valid member or member ID.' % argument) from None

        if not can_execute_action(ctx, ctx.author, m):
            raise commands.BadArgument('You cannot do this action on this user due to role hierarchy.')
        return m


class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.isdigit():
            member_id = int(argument, base=10)
            try:
                return await ctx.guild.fetch_ban(discord.Object(id=member_id))
            except discord.NotFound:
                raise commands.BadArgument('This member has not been banned before.') from None

        ban_list = await ctx.guild.bans()
        entity = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            raise commands.BadArgument('This member has not been banned before.')
        return entity


class ActionReason(commands.Converter):
    async def convert(self, ctx, argument):
        ret = '%s (ID: %s): %s' % (ctx.author, ctx.author.id, argument)

        if len(ret) > 512:
            reason_max = 512 - len(ret) + len(argument)
            raise commands.BadArgument('Reason is too long (%s/%s)' % (len(argument), reason_max))
        return ret


def safe_reason_append(base, to_append):
    appended = base + f'({to_append})'
    if len(appended) > 512:
        return base
    return appended


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _cleanup_strategy_simple(self, ctx, search):
        count = 0
        async for msg in ctx.history(limit=search, before=ctx.message):
            if msg.author == ctx.me:
                await msg.delete()
                count += 1
        return {'Bot': count}

    async def _cleanup_strategy(self, ctx, search):
        prefixes = tuple(self.bot.get_guild_prefixes(ctx.guild))  # could be easier if discord didn't suck

        def check(m):
            return m.author == ctx.me or m.content.startswith(prefixes)

        deleted = await ctx.channel.purge(limit=search, check=check, before=ctx.message)
        return Counter(m.author.display_name for m in deleted)

    @commands.command()
    @checks.has_permissions(manage_messages=True)
    async def cleanup(self, ctx, search=100):
        """Cleans up the bot's messages from the channel."""

        strategy = self._cleanup_strategy_simple
        if ctx.me.permissions_in(ctx.channel).manage_messages:
            strategy = self._cleanup_strategy

        spammers = await strategy(ctx, search)
        deleted = sum(spammers.values())
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            messages.append('')
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f'- **{author}**: {count}' for author, count in spammers)

        await ctx.send('\n'.join(messages), delete_after=10)

    @commands.command()
    @commands.guild_only()
    @checks.has_permissions(ban_members=True)
    async def ban(self, ctx, member: MemberID, *, reason: ActionReason = None):
        """Bans a member from the server.
        """

        if reason is None:
            reason = 'Action done by %s (ID: %s)' % (ctx.author, ctx.author.id)

        await ctx.guild.ban(member, reason=reason)
        await ctx.send('\N{OK HAND SIGN}')

    @commands.command()
    @commands.guild_only()
    @checks.has_permissions(kick_members=True)
    async def kick(self, ctx, member: MemberID, *, reason: ActionReason = None):
        """Kicks a member from the server.
        """

        if reason is None:
            reason = 'Action done by %s (ID: %s)' % (ctx.author, ctx.author.id)

        await ctx.guild.kick(member, reason=reason)
        await ctx.send('\N{OK HAND SIGN}')

    @commands.command()
    @commands.guild_only()
    @checks.has_permissions(ban_members=True)
    async def multiban(self, ctx, members: commands.Greedy[MemberID], *, reason: ActionReason = None):
        """Bans multiple members from the server.
        """

        if reason is None:
            reason = f'Action done by %s (ID: %s)' % (ctx.author, ctx.author.id)

        total_members = len(members)
        if total_members == 0:
            return await ctx.send('Missing members to ban.')

        confirm = await ctx.prompt(f'This will ban **{Plural(total_members):member}**. Are you sure?', reacquire=False)
        if not confirm:
            return await ctx.send('Aborting.')

        failed = 0
        for member in members:
            try:
                await ctx.guild.ban(member, reason=reason)
            except discord.HTTPException:
                failed += 1

        await ctx.send(f'Banned {total_members - failed}/{total_members} members.')


def setup(bot):
    bot.add_cog(Mod(bot))
