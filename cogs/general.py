import logging
import discord
from discord.ext import commands, menus
from .utils.embed import Embed
from .utils.paginator import ADBPages
from .utils import time, formats
from collections import Counter
import asyncio
import humanize
import unicodedata
import inspect
import os

log = logging.getLogger("cogs.general")


class BotHelpPageSource(menus.ListPageSource):
    def __init__(self, help_command, commands):
        # entries = [(cog, len(sub)) for cog, sub in commands.items()]
        # entries.sort(key=lambda t: (t[0].qualified_name, t[1]), reverse=True)
        super().__init__(entries=sorted(commands.keys(), key=lambda c: c.qualified_name), per_page=6)
        self.commands = commands
        self.help_command = help_command
        self.prefix = help_command.clean_prefix

    def format_commands(self, cog, commands):
        # A field can only have 1024 characters so we need to paginate a bit
        # just in case it doesn"t fit perfectly
        # However, we have 6 per page so I"ll try cutting it off at around 800 instead
        # Since there"s a 6000 character limit overall in the embed
        if cog.description:
            short_doc = cog.description.split("\n", 1)[0] + "\n"
        else:
            short_doc = "No help found...\n"

        current_count = len(short_doc)
        ending_note = "+%d not shown"
        ending_length = len(ending_note)

        page = []
        for command in commands:
            value = f"`{command.name}`"
            count = len(value) + 1 # The space
            if count + current_count < 800:
                current_count += count
                page.append(value)
            else:
                # If we"re maxed out then see if we can add the ending note
                if current_count + ending_length + 1 > 800:
                    # If we are, pop out the last element to make room
                    page.pop()

                # Done paginating so just exit
                break

        if len(page) == len(commands):
            # We"re not hiding anything so just return it as-is
            return short_doc + " ".join(page)

        hidden = len(commands) - len(page)
        return short_doc + " ".join(page) + "\n" + (ending_note % hidden)


    async def format_page(self, menu, cogs):
        prefix = menu.ctx.prefix
        description = f"Use \"{prefix}help command\" for more info on a command.\n" \
                      f"Use \"{prefix}help category\" for more info on a category.\n" \
                       "For more help, [join the help server](https://discord.gg/ycUPFpy)."

        embed = Embed(ctx=menu.ctx, title="Categories", description=description)

        for cog in cogs:
            commands = self.commands.get(cog)
            if commands:
                value = self.format_commands(cog, commands)
                embed.add_field(name=cog.qualified_name, value=value, inline=True)

        maximum = self.get_max_pages()
        embed.set_footer(text=f"Page {menu.current_page + 1}/{maximum}",
                         icon_url="https://cdn3.iconfinder.com/data/icons/popular-services-brands/512/github-512.png")
        return embed


class GroupHelpPageSource(menus.ListPageSource):
    def __init__(self, group, commands, *, prefix):
        super().__init__(entries=commands, per_page=6)
        self.group = group
        self.prefix = prefix
        self.title = f"{self.group.qualified_name} Commands"
        self.description = self.group.description

    async def format_page(self, menu, commands):
        embed = Embed(ctx=menu.ctx, title=self.title, description=self.description)

        for command in commands:
            signature = f"{command.qualified_name} {command.signature}"
            embed.add_field(name=signature, value=command.short_doc or "No help given...", inline=False)

        maximum = self.get_max_pages()
        if maximum > 1:
            embed.set_author(name=f"Page {menu.current_page + 1}/{maximum} ({len(self.entries)} commands)")

        embed.set_footer(text=f"Use \"{self.prefix}help command\" for more info on a command.",
                         icon_url="https://cdn3.iconfinder.com/data/icons/popular-services-brands/512/github-512.png")
        return embed


class HelpMenu(ADBPages):
    def __init__(self, source):
        super().__init__(source)

    @menus.button("\N{WHITE QUESTION MARK ORNAMENT}", position=menus.Last(5))
    async def show_bot_help(self, payload):
        """shows how to use the bot"""

        embed = Embed(ctx=payload.ctx, title="Using the bot", description="Hello! Welcome to the help page.")

        entries = (
            ("<argument>", "This means the argument is __**required**__."),
            ("[argument]", "This means the argument is __**optional**__."),
            ("[A|B]", "This means that it can be __**either A or B**__."),
            ("[argument...]", "This means you can have multiple arguments.\n" \
                              "Now that you know the basics, it should be noted that...\n" \
                              "__**You do not type in the brackets!**__")
        )

        embed.add_field(name="How do I use this bot?", value="Reading the bot signature is pretty simple.")

        for name, value in entries:
            embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text=f"We were on page {self.current_page + 1} before this message.")
        await self.message.edit(embed=embed)

        async def go_back_to_current_page():
            await asyncio.sleep(30.0)
            await self.show_page(self.current_page)

        self.bot.loop.create_task(go_back_to_current_page())


class PaginatedHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={
            "cooldown": commands.Cooldown(1, 3.0, commands.BucketType.member),
            "help": "Shows help about the bot, a command, or a category"
        })

    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(str(error.original))

    def get_command_signature(self, command):
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = "|".join(command.aliases)
            fmt = f"[{command.name}|{aliases}]"
            if parent:
                fmt = f"{parent} {fmt}"
            alias = fmt
        else:
            alias = command.name if not parent else f"{parent} {command.name}"
        return f"{alias} {command.signature}"

    async def send_bot_help(self, mapping):
        bot = self.context.bot
        entries = await self.filter_commands(bot.commands, sort=True)

        all_commands = {}
        for command in entries:
            if command.cog is None:
                continue
            try:
                all_commands[command.cog].append(command)
            except KeyError:
                all_commands[command.cog] = [command]


        menu = HelpMenu(BotHelpPageSource(self, all_commands))
        await menu.start(self.context)

    async def send_cog_help(self, cog):
        entries = await self.filter_commands(cog.get_commands(), sort=True)
        menu = HelpMenu(GroupHelpPageSource(cog, entries, prefix=self.clean_prefix))
        await menu.start(self.context)

    def common_command_formatting(self, embed_like, command):
        embed_like.title = self.get_command_signature(command)
        if command.description:
            embed_like.description = f"{command.description}\n\n{command.help}"
        else:
            embed_like.description = command.help or "No help found..."

    async def send_command_help(self, command):
        # No pagination necessary for a single command.
        embed = discord.Embed(colour=discord.Colour.blurple())
        self.common_command_formatting(embed, command)
        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        subcommands = group.commands
        if len(subcommands) == 0:
            return await self.send_command_help(group)

        entries = await self.filter_commands(subcommands, sort=True)
        if len(entries) == 0:
            return await self.send_command_help(group)

        source = GroupHelpPageSource(group, entries, prefix=self.clean_prefix)
        self.common_command_formatting(source, group)
        menu = HelpMenu(source)
        await menu.start(self.context)


class General(commands.Cog):
    """General commands to do simple stuff."""

    def __init__(self, bot):
        self.bot = bot
        self.old_help_command = bot.help_command
        bot.help_command = PaginatedHelpCommand()
        bot.help_command.cog = self

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
            ("Nickname:", f"{nick}"),
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
                return await ctx.error("Invalid Guild ID given.")
        else:
            guild = ctx.guild

        roles = [role.name.replace("@", "@\u200b") for role in guild.roles]

        # figure out what channels are "secret"
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
                info.append(f"<:yes:795341028458627122>: {label}")

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
            f"🟢 {member_by_status['online']} "
            f"🟡 {member_by_status['idle']} "
            f"🔴 {member_by_status['dnd']} "
            f"⚫	 {member_by_status['offline']}\n"
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
            f"Regular: {emoji_stats['regular']}/{guild.emoji_limit}\n"
            f"Animated: {emoji_stats['animated']}/{guild.emoji_limit}\n"
        )
        if emoji_stats["disabled"] or emoji_stats["animated_disabled"]:
            fmt = f"{fmt}Disabled: {emoji_stats['disabled']} regular, {emoji_stats['animated_disabled']} animated\n"

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
        if command is None:
            return await ctx.send(source_url)

        if command == "help":
            src = type(self.bot.help_command)
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command.replace(".", " "))
            if obj is None:
                return await ctx.error("Could not find command.")

            # since we found the command we"re looking for, presumably anyway, let"s
            # try to access the code itself
            src = obj.callback.__code__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        location = os.path.relpath(filename).replace("\\", "/")

        final_url = f"<{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>"
        await ctx.send(final_url)

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
