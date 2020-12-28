from discord.ext import commands


class NoChannelProvided(commands.CommandError):
    """Error raised when no suitable voice channel was supplied."""

    pass


class IncorrectChannelError(commands.CommandError):
    """Error raised when commands are issued outside of the players session channel."""

    pass


class NotConnected(commands.CommandError):
    """Error raised when a music player gets invoked, but no connection to a voice channel was established before."""

    pass


class RedditAPIError(commands.CommandError):
    """Error raised when the bot runs into an API error."""

    pass


class MemberNotFound(Exception):
    """Error raised when a Member couldn't be found by the id."""

    pass
