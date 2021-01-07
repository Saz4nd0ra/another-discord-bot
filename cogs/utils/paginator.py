import discord
from discord.ext import commands, menus
from discord.ext.commands import Paginator as CommandPaginator
from .embed import Embed
import asyncio


class ADBPages(menus.MenuPages):
    def __init__(self, source, **kwargs):
        super().__init__(source=source, check_embeds=True, **kwargs)

    async def finalize(self, timed_out):
        try:
            if timed_out:
                await self.message.clear_reactions()
            else:
                await self.message.delete()
        except discord.HTTPException:
            pass


class QueuePaginator(menus.ListPageSource):
    """Paginated queue."""

    def __init__(self, entries):
        super().__init__(entries, per_page=8)

    async def format_page(self, menu, page):
        embed = Embed(ctx=menu.ctx, title=f"Queue for {menu.ctx.channel.name}")
        embed.description = "\n".join(
            f"`{index}. {title}`" for index, title in enumerate(page, 1)
        )

        return embed


class TextPageSource(menus.ListPageSource):
    def __init__(self, text, *, prefix="```", suffix="```", max_size=2000):
        pages = CommandPaginator(prefix=prefix, suffix=suffix, max_size=max_size - 200)
        for line in text.split("\n"):
            pages.add_line(line)

        super().__init__(entries=pages, per_page=1)

    async def format_page(self, menu, content):
        maximum = self.get_max_pages()
        if maximum > 1:
            return f"{content}\nPage {menu.current_page + 1}/{maximum}"
        return content
