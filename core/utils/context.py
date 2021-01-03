from discord.ext import commands
import discord
import asyncio
import discord
import io
from .embed import Embed


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

    async def error(self, message: str, auto_delete: int = None):
        """Triggers our Error embed to send the error message needed."""
        e = Embed.error(
            ctx=self,
            title="Something went wrong.",
            description=message,
            colour=0xE82243,
            delete_after=auto_delete if auto_delete else auto_delete == None,
        )
        await self.send(embed=e)

    async def embed(self, message: str, auto_delete: int = None):
        """Sends a quick embed."""
        e = Embed(
            ctx=self,
            title=f"{self.prefix}{self.command.qualified_name}",
            description=message,
        )
        await self.send(
            embed=e,
            delete_after=auto_delete if auto_delete else auto_delete is None,
        )

    async def prompt(self, message, *, timeout=60.0, delete_after=True, reacquire=True, author_id=None):
        """An interactive reaction confirmation dialog.
        Parameters
        -----------
        message: str
            The message to show along with the prompt.
        timeout: float
            How long to wait before returning.
        delete_after: bool
            Whether to delete the confirmation message after we're done.
        reacquire: bool
            Whether to release the database connection and then acquire it
            again when we're done.
        author_id: Optional[int]
            The member who should respond to the prompt. Defaults to the author of the
            Context's message.
        Returns
        --------
        Optional[bool]
            ``True`` if explicit confirm,
            ``False`` if explicit deny,
            ``None`` if deny due to timeout
        """

        if not self.channel.permissions_for(self.me).add_reactions:
            raise RuntimeError("Bot does not have Add Reactions permission.")

        fmt = f"{message}\n\nReact with \N{WHITE HEAVY CHECK MARK} to confirm or \N{CROSS MARK} to deny."

        author_id = author_id or self.author.id
        msg = await self.send(fmt)

        confirm = None

        def check(payload):
            nonlocal confirm

            if payload.message_id != msg.id or payload.user_id != author_id:
                return False

            codepoint = str(payload.emoji)

            if codepoint == '\N{WHITE HEAVY CHECK MARK}':
                confirm = True
                return True
            elif codepoint == '\N{CROSS MARK}':
                confirm = False
                return True

            return False

        for emoji in ('\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}'):
            await msg.add_reaction(emoji)

        if reacquire:
            await self.release()

        try:
            await self.bot.wait_for('raw_reaction_add', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = None

        try:
            if reacquire:
                await self.acquire()

            if delete_after:
                await msg.delete()
        finally:
            return confirm

    def tick(self, opt, label=None):
        lookup = {
            True: '<:yes:795341028458627122>',
            False: '<:no:795341460647968769>',
            None: '<:greyTick:795341354036363294>',
        }
        emoji = lookup.get(opt, '<:redTick:330090723011592193>')
        if label is not None:
            return f'{emoji}: {label}'
        return emoji