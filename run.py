import logging
import asyncio
import os

from core.bot import ADB


def setup_logging():
    try:
        # __enter__
        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.WARNING)

        log = logging.getLogger()
        log.setLevel(logging.INFO)
        if not os.path.exists("logs/"):
            os.mkdir("logs/")
        handler = logging.FileHandler(
            filename="logs/adb.log", encoding="utf-8", mode="w"
        )
        dt_fmt = "%Y-%m-%d %H:%M:%S"
        fmt = logging.Formatter(
            "[{asctime}] [{levelname:<7}] {name}: {message}", dt_fmt, style="{"
        )
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield
    finally:
        # __exit__
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


def run_bot():
    log = logging.getLogger()
    log.info("Starting adb...")
    bot = ADB()
    bot.run()


def main():
    """Launches the bot."""
    loop = asyncio.get_event_loop()
    with setup_logging():
        run_bot()


if __name__ == "__main__":
    main()
