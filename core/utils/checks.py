from discord.ext import commands


def is_owner():
    async def predicate(ctx):
        if ctx.bot.config.owner_id == "auto" and ctx.author.id is ctx.bot.owner_id:
            return True
        elif ctx.author.id is ctx.bot.config.owner_id:
            return True
        else:
            return False

    return commands.check(predicate)


def not_dm():
    async def predicate(ctx):
        if not ctx.message.guild:
            raise commands.NoPrivateMessage()
        else:
            return True

    return commands.check(predicate)


def is_admin():
    async def predicate(ctx):
        if not ctx.message.guild:
            raise commands.NoPrivateMessage()
        elif ctx.author.guild_permissions.administrator:
            return True
        elif ctx.author.roles[1].id in ctx.bot.config.admin_role_ids:
            return True
        else:
            return False
            ctx.send("You do not have the necessary permissions to use that command.")

    return commands.check(predicate)


def is_mod():
    async def predicate(ctx):
        if not ctx.message.guild:
            raise commands.NoPrivateMessage()
        elif ctx.author.guild_permissions.delete_messages:
            return True
        elif ctx.author.roles[1].id in ctx.bot.config.mod_role_ids:
            return True
        else:
            return False
            ctx.send("You do not have the necessary permissions to use that command.")

    return commands.check(predicate)


def is_dev():
    async def predicate(ctx):
        if not ctx.message.guild:
            raise commands.NoPrivateMessage()
        elif ctx.author.id in ctx.bot.config.dev_ids:
            return True
        else:
            return False
            ctx.send("You do not have the necessary permissions to use that command.")

    return commands.check(predicate)
