from discord.ext import commands

from cogs.utils import formats


class Context(commands.Context):

    async def paginate(self, **kwargs) -> None:
        return await formats.Paginator(ctx=self, **kwargs).paginate()

    async def paginate_embed(self, **kwargs) -> None:
        return await formats.EmbedPaginator(ctx=self, **kwargs).paginate()

    async def paginate_embeds(self, **kwargs) -> None:
        return await formats.EmbedsPaginator(ctx=self, **kwargs).paginate()

    async def paginate_codeblock(self, **kwargs) -> None:
        return await formats.CodeBlockPaginator(ctx=self, **kwargs).paginate()