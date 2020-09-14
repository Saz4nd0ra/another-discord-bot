import discord
from discord.ext import commands
import asyncio
from ...utils.embed import Embed
from collections import Counter
from ...utils import checks
import shlex
import argparse
import re


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


class Mod(commands.Cog):
    """Commands for moderators in a guild."""

    def __init__(self, bot):
        self.bot = bot

    async def get_ban(self, name_or_id: str):
        """Get a ban in the guild."""
        for ban in await self.guild.bans():
            if name_or_id.isdigit():
                if ban.user.id == int(name_or_id):
                    return ban
            if str(ban.user).lower().startswith(name_or_id.lower()):
                return ban

    async def do_removal(self, ctx, limit, predicate, *, before=None, after=None):
        if limit > 2000:
            return await ctx.error(f'Too many messages to search given ({limit}/2000)')

        if before is None:
            before = ctx.message
        else:
            before = discord.Object(id=before)

        if after is not None:
            after = discord.Object(id=after)

        try:
            deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
        except discord.Forbidden as e:
            return await ctx.error('I do not have permissions to delete messages.')
        except discord.HTTPException as e:
            return await ctx.error(f'Error: {e} (try a smaller search?)')

        spammers = Counter(m.author.display_name for m in deleted)
        deleted = len(deleted)
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            messages.append('')
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f'**{name}**: {count}' for name, count in spammers)

        to_send = '\n'.join(messages)

        if len(to_send) > 2000:
            await ctx.embed(f'Successfully removed {deleted} messages.', 10)
        else:
            await ctx.embed(to_send, 10)

    @checks.is_mod()
    @commands.command()
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        """Kick a member from the guild"""
        await ctx.guild.kick(user, reason=reason)
        await ctx.embed(f"Done. {user.name} was kicked.")

    @checks.is_mod()
    @commands.command()
    async def ban(self, ctx, user: discord.Member, *, reason=None):
        """Ban a member from the guild"""
        await ctx.guild.ban(user, reason=reason)
        await ctx.embed(f"Done. {user.name} was banned.")

    @checks.is_mod()
    @commands.command()
    async def unban(self, ctx, name_or_id, *, reason=None):
        """Unban a member from the guild"""
        ban = await ctx.get_ban(name_or_id)
        if not ban:
            return await ctx.send("No user found.")
        await ctx.guild.unban(ban.user, reason=reason)
        await ctx.embed(f"Unbanned *{ban.user}* from the server.")

    @checks.is_mod()
    @commands.command()
    async def softban(self, ctx, member: discord.Member, *, reason=None):
        """Kicks a members and deletes their messages."""
        await member.ban(reason=f"Softban - {reason}")
        await member.unban(reason="Softban unban.")
        await ctx.embed(f"Done. {member.name} was softbanned.")

    @checks.is_mod()
    @commands.command()
    async def hackban(self, ctx, user_id: int, *, reason=None):
        """Bans a user that is currently not in the server.
        Only accepts user IDs."""
        await ctx.guild.ban(discord.Object(id=user_id), reason=reason)
        await ctx.embed(f"{self.bot.get_user(user_id)} just got hackbanned!")

    @checks.is_mod()
    @commands.command()
    async def mute(self, ctx, user: discord.Member, time: int = 15):
        """Mute a member in the guild"""
        secs = time * 60
        for channel in ctx.guild.channels: # muting
            if isinstance(channel, discord.TextChannel):
                await ctx.channel.set_permissions(user, send_messages=False)
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(user, connect=False)
        await ctx.embed(f"{user.mention} has been muted for {time} minutes.")
        await asyncio.sleep(secs)
        for channel in ctx.guild.channels: # unmuting
            if isinstance(channel, discord.TextChannel):
                await ctx.channel.set_permissions(user, send_messages=None)
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(user, connect=None)
        await ctx.embed(f"{user.mention} has been unmuted from the guild.")

    @checks.is_mod()
    @commands.command()
    async def unmute(self, ctx, user: discord.Member):
        """Unmute a member in the guild"""
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                await ctx.channel.set_permissions(user, send_messages=None)
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(user, connect=None)
        await ctx.embed(f"{user.mention} has been unmuted from the guild.")

    @checks.is_mod()
    @commands.command()
    async def warn(self, ctx, user: discord.Member, *, reason: str):
        """Warn a member via DMs"""
        warning = (
            f"You have been warned in **{ctx.guild}** by **{ctx.author}** for {reason}"
        )
        if not reason:
            warning = f"You have been warned in **{ctx.guild}** by **{ctx.author}**"
        try:
            await user.send(warning)
        except discord.Forbidden:
            return await ctx.send(
                "The user has disabled DMs for this guild or blocked the bot."
            )
        await ctx.embed(f"**{user}** has been **warned**")

    @checks.is_mod()
    @commands.command()
    async def removereactions(self, ctx, *, messageid: str):
        """Removes all reactions from a message."""
        message = await ctx.channel.get_message(messageid)
        await message.clear_reactions()
        await ctx.embed("Removed reactions.")

    @checks.is_mod()
    @commands.command()
    async def hierarchy(self, ctx):
        """Lists the role hierarchy of the server."""
        msg = f"Role hierarchy of {ctx.guild}:\n\n"
        roles = {}

        for role in ctx.guild.roles:
            if role.is_default():
                roles[role.position] = "everyone"
            else:
                roles[role.position] = role.name

        for role in sorted(roles.items(), reverse=True):
            msg += role[1] + "\n"
        await ctx.embed(msg)

    @checks.is_mod()
    @commands.command()
    async def addrole(self, ctx, member: discord.Member, *, rolename: str):
        """Adds a specified role to a specified user."""
        role = discord.utils.get(ctx.guild.roles, name=rolename)
        await member.add_roles(role)
        await ctx.embed(f"{member.mention} has been given `{role.name}`.")

    @checks.is_mod()
    @commands.command()
    async def removerole(self, ctx, member: discord.Member, *, rolename: str):
        """Removes a specified role from a specified user."""
        role = discord.utils.get(ctx.guild.roles, name=rolename)
        await member.remove_roles(role)
        await ctx.send(f"{member.mention} has been given `{role.name}`.")

    @checks.is_mod()
    @commands.command()
    async def purge(self, ctx, *, args: str):
        """An advanced purge command. Available args:
        `--user --contains --starts --ends --search --after --before
        --bot --embeds --files --emoji --reactions --or --not`
        """
        parser = Arguments(add_help=False, allow_abbrev=False)
        parser.add_argument('--user', nargs='+')
        parser.add_argument('--contains', nargs='+')
        parser.add_argument('--starts', nargs='+')
        parser.add_argument('--ends', nargs='+')
        parser.add_argument('--or', action='store_true', dest='_or')
        parser.add_argument('--not', action='store_true', dest='_not')
        parser.add_argument('--emoji', action='store_true')
        parser.add_argument('--bot', action='store_const', const=lambda m: m.author.bot)
        parser.add_argument('--embeds', action='store_const', const=lambda m: len(m.embeds))
        parser.add_argument('--files', action='store_const', const=lambda m: len(m.attachments))
        parser.add_argument('--reactions', action='store_const', const=lambda m: len(m.reactions))
        parser.add_argument('--search', type=int)
        parser.add_argument('--after', type=int)
        parser.add_argument('--before', type=int)

        try:
            args = parser.parse_args(shlex.split(args))
        except Exception as e:
            await ctx.send(str(e))
            return

        predicates = []
        if args.bot:
            predicates.append(args.bot)

        if args.embeds:
            predicates.append(args.embeds)

        if args.files:
            predicates.append(args.files)

        if args.reactions:
            predicates.append(args.reactions)

        if args.emoji:
            custom_emoji = re.compile(r'<:(\w+):(\d+)>')
            predicates.append(lambda m: custom_emoji.search(m.content))

        if args.user:
            users = []
            converter = commands.MemberConverter()
            for u in args.user:
                try:
                    user = await converter.convert(ctx, u)
                    users.append(user)
                except Exception as e:
                    await ctx.send(str(e))
                    return

            predicates.append(lambda m: m.author in users)

        if args.contains:
            predicates.append(lambda m: any(sub in m.content for sub in args.contains))

        if args.starts:
            predicates.append(lambda m: any(m.content.startswith(s) for s in args.starts))

        if args.ends:
            predicates.append(lambda m: any(m.content.endswith(s) for s in args.ends))

        op = all if not args._or else any
        def predicate(m):
            r = op(p(m) for p in predicates)
            if args._not:
                return not r
            return r

        if args.after:
            if args.search is None:
                args.search = 2000

        if args.search is None:
            args.search = 100

        args.search = max(0, min(2000, args.search)) # clamp from 0-2000
        await self.do_removal(ctx, args.search, predicate, before=args.before, after=args.after)


def setup(bot):
    bot.add_cog(Mod(bot))
