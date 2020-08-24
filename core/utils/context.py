from discord.ext import commands
import discord
import asyncio
import discord
import io


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def session(self):
        return self.bot.session

    async def show_help(self, command=None):
        """Shows the help command for the specified command if given."""
        cmd = self.bot.get_command("help")
        command = command or self.command.qualified_name
        await self.invoke(cmd, command=command)

    async def safe_send(self, content, *, escape_mentions=True, **kwargs):
        """Same as send except with some safe guards."""
        if escape_mentions:
            content = discord.utils.escape_mentions(content)

        if len(content) > 2000:
            fp = io.BytesIO(content.encode())
            kwargs.pop("file", None)
            return await self.send(
                file=discord.File(fp, filename="message_too_long.txt"), **kwargs
            )
        else:
            return await self.send(content)

    async def error(self, message):
        """Triggers our Error embed to send the error message needed."""
        e = discord.Embed(title="An error occurred:", message=message, color=0xe82243)
        await self.send(embed=e)
