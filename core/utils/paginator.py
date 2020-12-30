import discord
from discord.ext import commands, menus
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

    @menus.button("\N{PUBLIC ADDRESS LOUDSPEAKER}", position=menus.Last(6))
    async def announcements(self, payload):
        """Announcements go here"""

        embed = Embed(
            self.ctx,
            title=self.bot.announcement["title"],
            description=self.bot.announcement["message"],
        )

        await self.message.edit(content=None, embed=embed)

        async def go_back_to_current_page():
            await asyncio.sleep(30.0)
            await self.show_page(self.current_page)

        self.bot.loop.create_task(go_back_to_current_page())


