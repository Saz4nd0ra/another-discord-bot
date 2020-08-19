import discord
import typing
from discord.ext import commands
import asyncio
import datetime


class SimpleEmbed(discord.Embed):
    def __init__(
        self, message: typing.Union[commands.Context, discord.Message] = None, **kwargs
    ):
        super().__init__(**kwargs)
        asyncio.create_task(
            self.__ainit__(message, **kwargs)
        )  # basically creates a task to initiate our discord.Embed method

    async def __ainit__(self, message, **kwargs):
        if (
            "color" in kwargs
        ):  # if color is provided, set color, else use the discord blurple color
            self.colour = kwargs.get("color")
        else:
            self.color = discord.Color.blurple()
        if isinstance(message, commands.Context):
            message = message.message
        title = kwargs.get("title")
        description = kwargs.get("description")

        self.set_footer(
            icon_url="https://i.imgur.com/gFHBoZA.png",
            text="Saz4nd0ra/another-discord-bot",
        )


# Usage:
# from ...utils.embed import
#
#
# e = SimpleEmbed(description=foo, title=f'foor {bar}')
#
#
