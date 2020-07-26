from discord.ext import commands

from cogs.utils import paginators


class Context(commands.Context):

    async def paginate(self, **kwargs) -> None:
        return await paginators.Paginator(ctx=self, **kwargs).paginate()

    async def paginate_embed(self, **kwargs) -> None:
        return await paginators.EmbedPaginator(ctx=self, **kwargs).paginate()

    async def paginate_embeds(self, **kwargs) -> None:
        return await paginators.EmbedsPaginator(ctx=self, **kwargs).paginate()

    async def paginate_codeblock(self, **kwargs) -> None:
        return await paginators.CodeBlockPaginator(ctx=self, **kwargs).paginate()