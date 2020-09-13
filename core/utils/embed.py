import discord

from typing import Tuple


class Embed(discord.Embed):
    def __init__(self, ctx=None, *, title: str, **kwargs):
        super(Embed, self).__init__(**kwargs)

        if ctx:
            self.timestamp = ctx.message.created_at

        if ctx:
            author_image = ctx.bot.user.avatar_url
            self.set_author(name=title, icon_url=author_image)
        else:
            self.title = title

        # if kwargs have an argument called colour, set the embed to colour to that
        # else default to discord blurple
        if kwargs.get("colour"):
            self.colour = int(kwargs.get("colour"))
        else:
            self.colour = 0x7289DA

        self.description = kwargs.get("description")

        self.set_footer(
            text="Saz4nd0ra/another-discord-bot",
            icon_url="https://i.imgur.com/gFHBoZA.png",
        )

        if kwargs.get("image"):
            self.set_image(url=kwargs.get("image"))

        if kwargs.get("thumbnail"):
            self.set_thumbnail(url=kwargs.get("thumbnail"))

    def add_fields(self, *fields: Tuple[str, str]):
        for name, value in fields:
            self.add_field(name=name, value=value)
