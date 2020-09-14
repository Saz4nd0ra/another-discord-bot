from inspect import Parameter
import textwrap
import typing as t
from .embed import Embed

import discord
from discord.ext import commands, menus
import discord.utils


class HelpSource(menus.ListPageSource):
    """The Help menu."""

    def __init__(
        self,
        signature: t.Callable,
        filter_commands: t.Coroutine,
        ctx,
        prefix: str,
        author: discord.User,
        cogs: t.Dict[t.Optional[commands.Cog], t.List[commands.Command]],
    ) -> None:
        self.get_command_signature = signature
        self.filter_commands = filter_commands
        self.ctx = ctx
        self.prefix = prefix
        self.menu_author = author
        sorted_cogs = sorted(cogs, key=lambda cog: cog.qualified_name if cog else "ZZ")
        super().__init__(
            [(cog, cogs[cog]) for cog in sorted_cogs],
            per_page=1,
        )

    async def format_page(
        self,
        menu: menus.Menu,
        cog_tuple: t.Tuple[t.Optional[commands.Cog], t.List[commands.Command]],
    ) -> discord.Embed:
        """Format the pages."""
        cog, command_list = cog_tuple
        embed = Embed(
            ctx=self.ctx,
            title=textwrap.dedent(
                f"""
                Help for {cog.qualified_name if cog else 'unclassified commands'}
                Page {menu.current_page+1}/{self.get_max_pages()}
                """
            ),
            description=textwrap.dedent(
                f"""
                Help syntax : `<Required argument>`. `[Optional Argument]`
                Command prefix: `{self.prefix}`
                {cog.description if cog else ""}
                """
            ),
        )
        for command in await self.filter_commands(command_list):
            embed.add_field(
                name=f"{self.prefix}{self.get_command_signature(command)}",
                value=command.help,
                inline=False,
            )
        return embed


class HelpCommand(commands.HelpCommand):
    """The Help implementation."""

    def get_command_signature(self, command: commands.Command) -> str:
        """Retrieve the command's signature."""
        basis = f"{command.qualified_name}"
        for arg in command.clean_params.values():
            if arg.kind in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL):
                basis += f" [{arg.name}]"
            elif arg.annotation == t.Optional:
                basis += f" [{arg.name} = None]"
            elif isinstance(arg.annotation, commands.converter._Greedy):
                basis += f" [{arg.name} = (...)]"
            elif arg.default == Parameter.empty:
                basis += f" <{arg.name}>"
            else:
                basis += f" [{arg.name} = {arg.default}]"
        return basis

    async def send_bot_help(self, mapping: dict) -> None:
        """Send the global help."""
        ctx = self.context
        pages = menus.MenuPages(
            source=HelpSource(
                self.get_command_signature,
                self.filter_commands,
                ctx,
                ctx.prefix,
                ctx.author,
                mapping,
            ),
            clear_reactions_after=True,
        )
        await pages.start(ctx)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """Send help for a cog."""
        ctx = self.context
        prefix = ctx.prefix
        embed = Embed(
            ctx,
            title=cog.qualified_name,
            description=textwrap.dedent(
                f"""
                Help syntax : `<Required argument>`. `[Optional Argument]`
                Command prefix: `{prefix}`
                {cog.description}
                """
            ),
        )
        for command in await self.filter_commands(cog.get_commands()):
            embed.add_field(
                name=f"{prefix}{self.get_command_signature(command)}",
                value=command.help,
                inline=False,
            )
        await ctx.send(embed=embed)

    async def send_command_help(self, command: commands.Command) -> None:
        """Send help for a command."""
        ctx = self.context
        prefix = ctx.prefix
        embed = Embed(
            ctx,
            title=f"{prefix}{self.get_command_signature(command)}",
            description=textwrap.dedent(
                f"""
                Help syntax : `<Required arguments`.
                `[Optional Arguments]`
                {command.help}
                """
            ),
        )
        if command.aliases:
            embed.add_field(name="Aliases :", value="\n".join(command.aliases))
        await ctx.send(embed=embed)

    async def send_group_help(self, group: commands.Group) -> None:
        """Send help for a group."""
        ctx = self.context
        prefix = ctx.prefix
        embed = Embed(
            ctx,
            title=textwrap.dedent(
                f"""
                Help for group {prefix}
                {self.get_command_signature(group)}
                """
            ),
            description=textwrap.dedent(
                f"""
                Help syntax : `<Required arguments>`.
                `[Optional Arguments]`
                {group.help}
                """
            ),
        )
        for command in await self.filter_commands(group.commands, sort=True):
            embed.add_field(
                name=f"{prefix}{self.get_command_signature(command)}",
                value=command.help,
                inline=False,
            )
        await ctx.send(embed=embed)

    async def send_error_message(self, error: str) -> None:
        """Send an error message."""
        ctx = self.context
        await ctx.bot.httpcat(ctx, 404, error)


def setup(bot: commands.Bot) -> None:
    """Add the help command."""
    bot.old_help_command = bot.help_command
    bot.help_command = HelpCommand(
        verify_checks=False,
        command_attrs={"hidden": True},
    )


def teardown(bot: commands.Bot) -> None:
    """Remove the help command."""
    bot.help_command = bot.old_help_command
