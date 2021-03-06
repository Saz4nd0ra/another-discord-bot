from discord.ext import commands
from .utils import checks
from .utils.api import Rule34API, DanbooruAPI, SauceNaoAPI
from .utils.embed import Embed


class NSFW(commands.Cog):
    """Commands for degenerates. Please stick to the rules."""
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
        self.rule34 = Rule34API()
        self.danbooru = DanbooruAPI()
        self.saucenao = SauceNaoAPI()

    # TODO work on a blacklist system and user configs (yikes)
    @checks.is_nsfw_channel()
    @commands.command(aliases=["r34"])
    async def rule34(self, ctx, *, search):
        """Browse rule34.xxx. Only available in NSFW channels."""

        file, is_video, has_source = await self.rule34.get_random_r34(search)
        if is_video:
            embed = Embed(ctx, title="Video found.", thumbnail=file.preview_url)
        else:
            embed = Embed(ctx, title="Image found.", image=file.file_url)
        if has_source:
            embed.add_field(
                name="Sauce from Rule34:", value=f"[Click Here!]({file.source})"
            )
        embed.add_field(name="Image/Video:", value=f"[Click Here!]({file.file_url})")

        try:
            sauce = self.saucenao.get_sauce_from_url(file.file_url)
            embed.add_field(
                name="Sauce from SauceNao:", value=f"[Click Here!]({sauce.urls[0]})"
            )
        finally:
            await ctx.send(embed=embed)

    @checks.is_nsfw_channel()
    @commands.command()
    async def danbooru(self, ctx, *, search):
        """Browse danbooru.me. Only available in NSFW channels."""

        file, is_video, has_source = self.danbooru.get_random_danbooru(search)

        file_source = file["source"]
        file_preview = file["preview_file_url"]
        file_url = file["file_url"]
        # TODO work on filtering videos, so we can actually send them
        if is_video:
            embed = Embed(ctx, title="Video found.", thumbnail=file_preview)
        else:
            embed = Embed(ctx, title="Image found.", image=file_url)
        if has_source:
            embed.add_field(
                name="Sauce from Danbooru:", value=f"[Click Here!]({file_source})"
            )
        embed.add_field(name="Image/Video:", value=f"[Click Here!]({file_url})")

        try:
            sauce = self.saucenao.get_sauce_from_url(file.file_url)
            embed.add_field(
                name="Sauce from SauceNao:", value=f"[Click Here!]({sauce.urls[0]})"
            )
        finally:
            await ctx.send(embed=embed)

    @checks.is_nsfw_channel()
    @commands.command(aliases=["sauce"])
    async def saucenao(self, ctx, *, url):
        """Get the sauce from pictures via an URL or file. Only available in NSFW channels."""

        try:
            sauce = self.saucenao.get_sauce_from_url(url)
            embed = Embed(ctx, title="Sauce found.", image=url)
            embed.add_fields(
                ("Author:", f"{sauce.author}"),
                ("Similarity:", f"{round(sauce.similarity)}%"),
            )
            embed.add_field(name="Link:", value=f"[Click Here!]({sauce.urls[0]})")
            try:
                await ctx.message.delete()
            except:
                pass
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.error("Something went wrong with the API.", 10)


def setup(bot):
    bot.add_cog(NSFW(bot))
