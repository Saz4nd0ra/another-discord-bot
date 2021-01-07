import logging
import discord
from discord.ext import commands
from .utils.embed import Embed
from .utils import time, formats
from collections import Counter
import random
import humanize
import unicodedata
import inspect
import os

log = logging.getLogger("cogs.general")


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

        embed = Embed(ctx, title=f"User: {user.name}", thumbnail=user.avatar_url)

        if hasattr(user, "nick"):
            nick = user.nick
        else:
            nick = user.name

        embed.add_fields(
            ("Username:", f"{user}"),
            ("Nickname:", f"{user.nick}"),
            ("ID:", f"{user.id}"),
            ("Created:", f"{humanize.naturaldate(user.created_at)}"),
            ("Joined:", f"{humanize.naturaldate(user.joined_at)}"),
            ("Roles:", f"{show_roles}"),
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def serverinfo(self, ctx, *, guild_id: int = None):
        """Shows info about the current server."""

        if guild_id is not None and await self.bot.is_owner(ctx.author):
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                return await ctx.send(f"Invalid Guild ID given.")
        else:
            guild = ctx.guild

        roles = [role.name.replace("@", "@\u200b") for role in guild.roles]

        # figure out what channels are 'secret'
        everyone = guild.default_role
        everyone_perms = everyone.permissions.value
        secret = Counter()
        totals = Counter()
        for channel in guild.channels:
            allow, deny = channel.overwrites_for(everyone).pair()
            perms = discord.Permissions((everyone_perms & ~deny.value) | allow.value)
            channel_type = type(channel)
            totals[channel_type] += 1
            if not perms.read_messages:
                secret[channel_type] += 1
            elif isinstance(channel, discord.VoiceChannel) and (
                not perms.connect or not perms.speak
            ):
                secret[channel_type] += 1

        member_by_status = Counter(str(m.status) for m in guild.members)

        embed = Embed(
            ctx,
            title=guild.name,
            description=f"**ID**: {guild.id}\n**Owner**: {guild.owner}",
            thumbnail=guild.icon_url,
        )
        embed.description = f"**ID**: {guild.id}\n**Owner**: {guild.owner}"
        if guild.icon:
            embed.set_thumbnail(url=guild.icon_url)

        channel_info = []
        key_to_emoji = {
            discord.TextChannel: ":keyboard:",
            discord.VoiceChannel: ":speaker:",
        }
        for key, total in totals.items():
            secrets = secret[key]
            try:
                emoji = key_to_emoji[key]
            except KeyError:
                continue

            if secrets:
                channel_info.append(f"{emoji} {total} ({secrets} locked)")
            else:
                channel_info.append(f"{emoji} {total}")

        info = []
        features = set(guild.features)
        all_features = {
            "PARTNERED": "Partnered",
            "VERIFIED": "Verified",
            "DISCOVERABLE": "Server Discovery",
            "COMMUNITY": "Community Server",
            "FEATURABLE": "Featured",
            "WELCOME_SCREEN_ENABLED": "Welcome Screen",
            "INVITE_SPLASH": "Invite Splash",
            "VIP_REGIONS": "VIP Voice Servers",
            "VANITY_URL": "Vanity Invite",
            "COMMERCE": "Commerce",
            "LURKABLE": "Lurkable",
            "NEWS": "News Channels",
            "ANIMATED_ICON": "Animated Icon",
            "BANNER": "Banner",
        }

        for feature, label in all_features.items():
            if feature in features:
                info.append(f"{ctx.tick(True)}: {label}")

        if info:
            embed.add_field(name="Features", value="\n".join(info))

        embed.add_field(name="Channels", value="\n".join(channel_info))

        if guild.premium_tier != 0:
            boosts = (
                f"Level {guild.premium_tier}\n{guild.premium_subscription_count} boosts"
            )
            last_boost = max(
                guild.members, key=lambda m: m.premium_since or guild.created_at
            )
            if last_boost.premium_since is not None:
                boosts = f"{boosts}\nLast Boost: {last_boost} ({time.human_timedelta(last_boost.premium_since, accuracy=2)})"
            embed.add_field(name="Boosts", value=boosts, inline=False)

        bots = sum(m.bot for m in guild.members)
        fmt = (
            f'🟢 {member_by_status["online"]} '
            f'🟡 {member_by_status["idle"]} '
            f'🔴 {member_by_status["dnd"]} '
            f'⚫	 {member_by_status["offline"]}\n'
            f"Total: {guild.member_count} ({formats.plural(bots):bot})"
        )

        embed.add_field(name="Members", value=fmt, inline=False)
        embed.add_field(
            name="Roles",
            value=", ".join(roles) if len(roles) < 10 else f"{len(roles)} roles",
        )

        emoji_stats = Counter()
        for emoji in guild.emojis:
            if emoji.animated:
                emoji_stats["animated"] += 1
                emoji_stats["animated_disabled"] += not emoji.available
            else:
                emoji_stats["regular"] += 1
                emoji_stats["disabled"] += not emoji.available

        fmt = (
            f'Regular: {emoji_stats["regular"]}/{guild.emoji_limit}\n'
            f'Animated: {emoji_stats["animated"]}/{guild.emoji_limit}\n'
        )
        if emoji_stats["disabled"] or emoji_stats["animated_disabled"]:
            fmt = f'{fmt}Disabled: {emoji_stats["disabled"]} regular, {emoji_stats["animated_disabled"]} animated\n'

        fmt = f"{fmt}Total Emoji: {len(guild.emojis)}/{guild.emoji_limit*2}"
        embed.add_field(name="Emoji", value=fmt, inline=False)
        embed.add_field(name="Created:", value=guild.created_at)
        await ctx.send(embed=embed)

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
        branch = "dev"
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

    @commands.command()
    async def invite(self, ctx):
        """Joins a server."""
        perms = discord.Permissions.none()
        perms.read_messages = True
        perms.external_emojis = True
        perms.send_messages = True
        perms.manage_roles = True
        perms.manage_channels = True
        perms.ban_members = True
        perms.kick_members = True
        perms.manage_messages = True
        perms.embed_links = True
        perms.read_message_history = True
        perms.attach_files = True
        perms.add_reactions = True
        perms.speak = True
        perms.move_members = True
        await ctx.send(f"<{discord.utils.oauth_url(self.bot.client_id, perms)}>")

    @commands.command()
    async def bug(self, ctx, *, command: str = None):
        """Report a bug to the owner of the bot instance."""

        if self.bot.config.owner_id == "auto":
            owner_id = ctx.bot.owner_id
        else:
            owner_id = self.bot.config.owner_id

        owner = await self.bot.get_user_info(owner_id)

        await self.bot.send_message(
            owner, f"{ctx.message.author} ran into an error. Used command: {command}."
        )
        await ctx.embed("Thank you, the message has been sent.")


def setup(bot):
    bot.add_cog(General(bot))
