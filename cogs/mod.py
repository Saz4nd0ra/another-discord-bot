import discord
from discord.ext import commands
import asyncio
from .utils.embed import Embed
from collections import Counter
from .utils import checks
import shlex
import argparse
import re


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


async def resolve_member(
    guild, member_id
):  # this returns a member when passing an id, could be useful quite often
    member = guild.get_member(member_id)
    if member is None:
        if guild.chunked:
            pass
        try:
            member = await guild.fetch_member(member_id)
        except discord.NotFound:
            pass
    return member


def can_execute_action(
    ctx, user, target
):  # checks if the bot is allowed to ban the member
    return (
        user.id == ctx.bot.owner_id
        or user == ctx.guild.owner
        or user.top_role > target.top_role
    )


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                member_id = int(argument, base=10)
                m = await resolve_member(ctx.guild, member_id)
            except ValueError:
                raise commands.BadArgument(
                    f"{argument} is not a valid member or member ID."
                ) from None
            except Exception as e:
                # hackban case
                return type(
                    "_Hackban",
                    (),
                    {"id": member_id, "__str__": lambda s: f"Member ID {s.id}"},
                )()

        if not can_execute_action(ctx, ctx.author, m):
            raise commands.BadArgument(
                "You cannot do this action on this user due to role hierarchy."
            )
        return m


class ActionReason(commands.Converter):
    async def convert(self, ctx, argument):
        ret = f"{ctx.author} (ID: {ctx.author.id}): {argument}"

        if len(ret) > 512:
            reason_max = 512 - len(ret) + len(argument)
            raise commands.BadArgument(
                f"Reason is too long ({len(argument)}/{reason_max})"
            )
        return ret


def safe_reason_append(base, to_append):
    appended = base + f"({to_append})"
    if len(appended) > 512:
        return base
    return appended


class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.isdigit():
            member_id = int(argument, base=10)
            try:
                return await ctx.guild.fetch_ban(discord.Object(id=member_id))
            except discord.NotFound:
                raise commands.BadArgument(
                    "This member has not been banned before."
                ) from None

        ban_list = await ctx.guild.bans()
        ban = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

        if ban is None:
            raise commands.BadArgument("This member has not been banned before.")
        return ban


class Mod(commands.Cog):
    """Commands for moderators in a guild."""

    def __init__(self, bot):
        self.bot = bot

    async def do_removal(self, ctx, limit, predicate, *, before=None, after=None):
        if limit > 2000:
            return await ctx.error(f"Too many messages to search given ({limit}/2000)")

        if before is None:
            before = ctx.message
        else:
            before = discord.Object(id=before)

        if after is not None:
            after = discord.Object(id=after)

        try:
            deleted = await ctx.channel.purge(
                limit=limit, before=before, after=after, check=predicate
            )
        except discord.Forbidden as e:
            return await ctx.error("I do not have permissions to delete messages.")
        except discord.HTTPException as e:
            return await ctx.error(f"Error: {e} (try a smaller search?)")

        spammers = Counter(m.author.display_name for m in deleted)
        deleted = len(deleted)
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            messages.append("")
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f"**{name}**: {count}" for name, count in spammers)

        to_send = "\n".join(messages)

        if len(to_send) > 2000:
            await ctx.embed(f"Successfully removed {deleted} messages.", 10)
        else:
            await ctx.embed(to_send, 10)

    @checks.is_mod()
    @commands.command()
    async def kick(self, ctx, member: MemberID, *, reason: ActionReason = None):
        """Kicks a member from the server."""

        if reason is None:
            reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"

        await ctx.guild.kick(member, reason=reason)
        await ctx.embed(f"**{member}** was kicked.")

    @checks.is_mod()
    @commands.command()
    async def ban(self, ctx, member: MemberID, *, reason: ActionReason = None):
        """Bans a member from the server."""

        if reason is None:
            reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"

        await ctx.guild.ban(member, reason=reason)
        await ctx.embed(f"**{member}** was banned.")

    @checks.is_mod()
    @commands.command()
    async def unban(self, ctx, member: BannedMember, *, reason: ActionReason = None):
        """Unbans a member from the server."""

        if reason is None:
            reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"

        await ctx.guild.unban(member.user, reason=reason)
        if member.reason:
            await ctx.embed(
                f"Unbanned {member.user} (ID: {member.user.id}), previously banned for {member.reason}."
            )
        else:
            await ctx.embed(f"Unbanned {member.user} (ID: {member.user.id}).")

    @checks.is_mod()
    @commands.command()
    async def softban(self, ctx, member: MemberID, *, reason: ActionReason = None):
        """Soft bans a member from the server."""

        if reason is None:
            reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"

        await ctx.guild.ban(member, reason=reason)
        await ctx.guild.unban(member, reason=reason)
        await ctx.embed(f"**{member}** was softbanned.")

    @checks.is_mod()
    @commands.command()
    async def mute(self, ctx, member: MemberID, time: int = 15):
        """Mute a member in the guild"""
        secs = time * 60
        for channel in ctx.guild.channels:  # muting
            if isinstance(channel, discord.TextChannel):
                await ctx.channel.set_permissions(member, send_messages=False)
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(member, connect=False)
        await ctx.embed(f"**{member}** has been muted for {time} minutes.")
        await asyncio.sleep(secs)
        for channel in ctx.guild.channels:  # unmuting
            if isinstance(channel, discord.TextChannel):
                await ctx.channel.set_permissions(member, send_messages=None)
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(member, connect=None)
        await ctx.embed(f"**{member}** has been unmuted from the guild.")

    # TODO: rework the un/mute command
    @checks.is_mod()
    @commands.command()
    async def unmute(self, ctx, member: MemberID):
        """Unmute a member in the guild"""
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                await ctx.channel.set_permissions(member, send_messages=None)
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(member, connect=None)
        await ctx.embed(f"**{member}** has been unmuted from the guild.")

    @checks.is_mod()
    @commands.command()
    async def warn(self, ctx, member: MemberID, *, reason: str):
        """Warn a member via DMs"""
        warning = (
            f"You have been warned in **{ctx.guild}** by **{ctx.author}** for {reason}"
        )
        if not reason:
            warning = f"You have been warned in **{ctx.guild}** by **{ctx.author}**"
        try:
            await member.send(warning)
        except discord.Forbidden:
            return await ctx.send(
                "The user has disabled DMs for this guild or blocked the bot."
            )
        await ctx.embed(f"**{member}** has been **warned**")

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
    async def addrole(self, ctx, member: MemberID, *, rolename: str):
        """Adds a specified role to a specified user."""
        role = discord.utils.get(ctx.guild.roles, name=rolename)
        await member.add_roles(role)
        await ctx.embed(f"**{member}** has been given `{role.name}`.")

    @checks.is_mod()
    @commands.command()
    async def removerole(self, ctx, member: MemberID, *, rolename: str):
        """Removes a specified role from a specified user."""
        role = discord.utils.get(ctx.guild.roles, name=rolename)
        await member.remove_roles(role)
        await ctx.send(f"**{member}** has been given `{role.name}`.")

    @checks.is_mod()
    @commands.command()
    async def purge(self, ctx, *, args: str):
        """An advanced purge command. Available args:
        `--user --contains --starts --ends --search --after --before
        --bot --embeds --files --emoji --reactions --or --not`
        """
        parser = Arguments(add_help=False, allow_abbrev=False)
        parser.add_argument("--user", nargs="+")
        parser.add_argument("--contains", nargs="+")
        parser.add_argument("--starts", nargs="+")
        parser.add_argument("--ends", nargs="+")
        parser.add_argument("--or", action="store_true", dest="_or")
        parser.add_argument("--not", action="store_true", dest="_not")
        parser.add_argument("--emoji", action="store_true")
        parser.add_argument("--bot", action="store_const", const=lambda m: m.author.bot)
        parser.add_argument(
            "--embeds", action="store_const", const=lambda m: len(m.embeds)
        )
        parser.add_argument(
            "--files", action="store_const", const=lambda m: len(m.attachments)
        )
        parser.add_argument(
            "--reactions", action="store_const", const=lambda m: len(m.reactions)
        )
        parser.add_argument("--search", type=int)
        parser.add_argument("--after", type=int)
        parser.add_argument("--before", type=int)

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
            custom_emoji = re.compile(r"<:(\w+):(\d+)>")
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
            predicates.append(
                lambda m: any(m.content.startswith(s) for s in args.starts)
            )

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

        args.search = max(0, min(2000, args.search))  # clamp from 0-2000
        await self.do_removal(
            ctx, args.search, predicate, before=args.before, after=args.after
        )


def setup(bot):
    bot.add_cog(Mod(bot))
