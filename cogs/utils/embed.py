import discord
import datetime
from typing import Tuple


class Embed(discord.Embed):
    def __init__(self, ctx, title, colour=0x7289DA, timestamp=None, **kwargs):
        super(Embed, self).__init__(
            colour=colour, timestamp=timestamp or datetime.datetime.utcnow(), **kwargs
        )

        self.timestamp = ctx.message.created_at
        self.set_author(
            name=title,
            icon_url=ctx.author.avatar_url, url="https://github.com/Saz4nd0ra/another-discord-bot"
        )

        self.description = kwargs.get("description")

        self.set_footer(
            text="Saz4nd0ra/another-discord-bot",
            icon_url=ctx.bot.user.avatar_url,
        )

        if kwargs.get("image"):
            self.set_image(url=kwargs.get("image"))

        if kwargs.get("thumbnail"):
            self.set_thumbnail(url=kwargs.get("thumbnail"))

    def add_fields(self, *fields: Tuple[str, str]):
        for name, value in fields:
            self.add_field(name=name, value=value)

    @classmethod
    def error(cls, colour=0xF5291B, **kwargs):
        return cls(colour=colour, **kwargs)

    @classmethod
    def warning(cls, colour=0xF55C1B, **kwargs):
        return cls(colour=colour, **kwargs)
