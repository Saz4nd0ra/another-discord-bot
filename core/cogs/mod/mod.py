import discord
from discord.ext import commands
import asyncio
from ...utils.embed import Embed
from ...utils import checks


class Mod(commands.Cog):
    """Commands for moderators in a guild."""

    def __init__(self, bot):
        self.bot = bot

    async def get_ban(self, name_or_id: str):
        """Get a ban in the guild."""
        for ban in await self.guild.bans():
            if name_or_id.isdigit():
                if ban.user.id == int(name_or_id):
                    return ban
            if str(ban.user).lower().startswith(name_or_id.lower()):
                return ban

    @checks.is_mod()
    @commands.command()
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        """Kick a member from the guild"""
        await ctx.guild.kick(user, reason=reason)
        await ctx.embed(f"Done. {user.name} was kicked.")

    @checks.is_mod()
    @commands.command()
    async def ban(self, ctx, user: discord.Member, *, reason=None):
        """Ban a member from the guild"""
        await ctx.guild.ban(user, reason=reason)
        await ctx.embed(f"Done. {user.name} was banned.")

    @checks.is_mod()
    @commands.command()
    async def unban(self, ctx, name_or_id, *, reason=None):
        """Unban a member from the guild"""
        ban = await ctx.get_ban(name_or_id)
        if not ban:
            return await ctx.send("No user found.")
        await ctx.guild.unban(ban.user, reason=reason)
        await ctx.embed(f"Unbanned *{ban.user}* from the server.")

    @checks.is_mod()
    @commands.command()
    async def softban(self, ctx, member: discord.Member, *, reason=None):
        """Kicks a members and deletes their messages."""
        await member.ban(reason=f"Softban - {reason}")
        await member.unban(reason="Softban unban.")
        await ctx.embed(f"Done. {member.name} was softbanned.")

    @checks.is_mod()
    @commands.command()
    async def hackban(self, ctx, user_id: int, *, reason=None):
        """Bans a user that is currently not in the server.
        Only accepts user IDs."""
        await ctx.guild.ban(discord.Object(id=user_id), reason=reason)
        await ctx.embed(f"{self.bot.get_user(user_id)} just got hackbanned!")

    @checks.is_mod()
    @commands.command()
    async def mute(self, ctx, user: discord.Member, time: int = 15):
        """Mute a member in the guild"""
        secs = time * 60
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                await ctx.channel.set_permissions(user, send_messages=False)
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(user, connect=False)
        await ctx.embed(f"{user.mention} has been muted for {time} minutes.")
        await asyncio.sleep(secs)
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                await ctx.channel.set_permissions(user, send_messages=None)
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(user, connect=None)
        await ctx.embed(f"{user.mention} has been unmuted from the guild.")

    @checks.is_mod()
    @commands.command()
    async def unmute(self, ctx, user: discord.Member):
        """Unmute a member in the guild"""
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                await ctx.channel.set_permissions(user, send_messages=None)
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(user, connect=None)
        await ctx.embed(f"{user.mention} has been unmuted from the guild.")

    @checks.is_mod()
    @commands.command()
    async def warn(self, ctx, user: discord.Member, *, reason: str):
        """Warn a member via DMs"""
        warning = (
            f"You have been warned in **{ctx.guild}** by **{ctx.author}** for {reason}"
        )
        if not reason:
            warning = f"You have been warned in **{ctx.guild}** by **{ctx.author}**"
        try:
            await user.send(warning)
        except discord.Forbidden:
            return await ctx.send(
                "The user has disabled DMs for this guild or blocked the bot."
            )
        await ctx.embed(f"**{user}** has been **warned**")

    @checks.is_mod()
    @commands.command()
    async def removereactions(self, ctx, *, messageid: str):
        """Removes all reactions from a message."""
        message = await ctx.channel.get_message(messageid)
        await message.clear_reactions()
        await ctx.embed("Removed reactions.")

    @checks.is_mod()
    @commands.command()
    async def hierarchy(self, ctx):
        """Lists the role hierarchy of the server."""
        msg = f"Role hierarchy of {ctx.guild}:\n\n"
        roles = {}

        for role in ctx.guild.roles:
            if role.is_default():
                roles[role.position] = "everyone"
            else:
                roles[role.position] = role.name

        for role in sorted(roles.items(), reverse=True):
            msg += role[1] + "\n"
        await ctx.embed(msg)

    @checks.is_mod()
    @commands.command()
    async def addrole(self, ctx, member: discord.Member, *, rolename: str):
        """Adds a specified role to a specified user."""
        role = discord.utils.get(ctx.guild.roles, name=rolename)
        await member.add_roles(role)
        await ctx.embed(f"{member.mention} has been given `{role.name}`.")

    @checks.is_mod()
    @commands.command()
    async def removerole(self, ctx, member: discord.Member, *, rolename: str):
        """Removes a specified role from a specified user."""
        role = discord.utils.get(ctx.guild.roles, name=rolename)
        await member.remove_roles(role)
        await ctx.send(f"{member.mention} has been given `{role.name}`.")


def setup(bot):
    bot.add_cog(Mod(bot))
