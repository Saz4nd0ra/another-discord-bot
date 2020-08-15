import sys
import click
import logging
import asyncio
import discord
import traceback
import importlib
import contextlib
import subprocess
import os

from bot import ADB, initial_extensions

from pathlib import Path

from cogs.utils.config import Config
config = Config()

@contextlib.contextmanager
def setup_logging():
    try:
        # __enter__
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)

        log = logging.getLogger()
        log.setLevel(logging.INFO)
        if not os.path.exists('logs/'):
            os.mkdir('logs/')
        handler = logging.FileHandler(filename='logs/adb.log', encoding='utf-8', mode='w')
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield
    finally:
        # __exit__
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)

def start_lavalink_node():
    log = logging.getLogger()
    log.info('Starting lavalink node...')
    subprocess.Popen(['java', '-jar', '-Xms512M','-Xmx512M','lavalink/Lavalink.jar'],
                     stdout=asyncio.subprocess.PIPE,
                     stderr=asyncio.subprocess.STDOUT)

def run_bot():
    log = logging.getLogger()
    log.info('Starting adb...')
    bot = ADB()
    bot.run()


@click.group(invoke_without_command=True, options_metavar='[options]')
@click.pass_context
def main(ctx):
    """Launches the bot."""
    start_lavalink_node()
    if ctx.invoked_subcommand is None:
        loop = asyncio.get_event_loop()
        with setup_logging():
            run_bot()

if __name__ == '__main__':
    main()
