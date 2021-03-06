from discord.ext import commands
import logging

log = logging.getLogger("utils.checks")


async def check_guild_permissions(ctx, perms, *, check=all):

    resolved = ctx.author.guild_permissions
    return check(
        getattr(resolved, name, None) == value for name, value in perms.items()
    )


def is_owner():
    async def predicate(ctx):
        if ctx.bot.config.owner_id == "auto" and ctx.author.id == ctx.bot.owner_id:
            return True
        elif str(ctx.author.id) == ctx.bot.config.owner_id:
            return True
        else:
            return False

    return commands.check(predicate)


def is_admin():
    async def predicate(ctx):
        if await check_guild_permissions(ctx, {"administrator": True}):
            return True
        elif is_owner() == True:  # bypass for owner
            log.info("Owner used admin command.")
            return True
        else:
            return False

    return commands.check(predicate)


def is_mod():
    async def predicate(ctx):
        if await check_guild_permissions(ctx, {"manage_guild": True}):
            return True
        elif is_admin():
            return True
        elif is_owner():  # again, bypass for owner
            log.info("Owner used mod command.")
            return True
        else:
            return False

    return commands.check(predicate)


def is_dev():
    async def predicate(ctx):
        if str(ctx.author.id) in ctx.bot.config.dev_ids:
            return True
        elif is_owner() == True:  # again, bypass for owner
            log.info("Owner used developer command.")
            return True
        else:
            return False

    return commands.check(predicate)


def is_nsfw_channel():
    async def predicate(ctx):
        if ctx.message.guild:
            if ctx.channel.is_nsfw():
                return True
            else:
                return False
        else:
            return True

    return commands.check(predicate)
