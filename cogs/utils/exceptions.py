import logging


class ADBExcpetion(Exception):
    def __init__(self, ctx, message, *, expire_in=0):
        super().__init__(ctx, message)
        self.ctx = ctx
        self._message = message
        self.expire_in = expire_in

    @property
    def message(self):
        return self._message


# Something went wrong during processing of a command
class CommandError(ADBExcpetion):
    pass


# The given member could not be found.
class MemberNotFound(ADBExcpetion):
    pass


# There was no channel provided for the bot to join.
class NoChannelProvided(ADBExcpetion):
    pass


# Something went wrong when parsing the argument(s)
class ArgumentError(ADBExcpetion):
    pass


# The command is not available. (Possible because you aren't on a server).
class CommandNotAvailable(ADBExcpetion):
    @property
    def message(self):
        return "This command is not available.\nAdditional Info: " + self._message


# The user doesn't have permission to use this command
class PermissionsError(CommandError):
    @property
    def message(self):
        return (
            "You don't have permission to use that command.\nAdditional Info: "
            + self._message
        )
