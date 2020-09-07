import discord
from discord.ext import commands
import logging

log = logging.getLogger("ADB Exceptions")


class NoChannelProvided(commands.CommandError):
    """Error raised when no suitable voice channel was supplied."""

    log.error("A command failed, because there was no Channel provided.")
    pass


class IncorrectChannelError(commands.CommandError):
    """Error raised when commands are issued outside of the players session channel."""

    log.error("A command failed, because the provided channel doesn't exist.")
    pass


class NotConnected(commands.CommandError):
    """Error raised when a music player gets invoked, but no connection to a voice channel was established before."""

    log.error("A player was invoked, but there was no channel connection available.")
    pass


class RedditAPIError(commands.CommandError):
    """Error raised when the bot runs into an API error."""

    log.error("There was an error when talking to the Reddit API.")
    pass
