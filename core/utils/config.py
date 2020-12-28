import logging
import os
import shutil
import codecs
from configparser import RawConfigParser

log = logging.getLogger("config")


# TODO maybe add a fallback, in case the user forgets to set a setting
class Config:
    def __init__(self):
        config = RawConfigParser(interpolation=None)
        if not os.path.exists("config/options.ini"):
            shutil.copyfile("config/example_options.ini", "config/options.ini")

        config.read("config/options.ini", encoding="utf-8")
        confsections = {
            "Credentials",
            "IDs",
            "Bot",
            "Music",
            "Reddit",
        }.difference(config.sections())

        if confsections:
            raise Exception(
                log.error(
                    "Config sections altered!\n"
                    "Make sure you have a correctly formatted config!"
                )
            )

        self.login_token = config.get("Credentials", "Token")

        self.privileged_users = config.get("IDs", "PrivilegedUsers")
        self.admin_role_ids = config.get("IDs", "AdminRoleIDs")
        self.mod_role_ids = config.get("IDs", "ModRoleIDs")
        self.owner_id = config.get("IDs", "OwnerID")
        self.dev_ids = config.get("IDs", "DevIDs")

        self.prefix = config.get("Bot", "Prefix")
        self.enable_msg_logging = config.getboolean("Bot", "EnableMSGLogging")
        self.msg_logging_channel = config.get("Bot", "LoggingChannel")
        self.blacklisted_ids = config.get("Bot", "BlacklistedIDs")

        self.ll_host = config.get("Music", "LavalinkHost")
        self.ll_port = config.get("Music", "LavalinkPort")
        self.ll_passwd = config.get("Music", "LavalinkPassword")

        self.enable_redditembed = config.getboolean("Reddit", "RedditEmbed")
        self.praw_username = config.get("Reddit", "PrawUsername")
        self.praw_password = config.get("Reddit", "PrawPassword")
        self.praw_secret = config.get("Reddit", "PrawSecret")
        self.praw_clientid = config.get("Reddit", "PrawClientID")


# TODO need to implement a fallback, in case the user fucks something up
class FallbackConfig:

    token = None
    ignored_ids = set()
    dev_ids = set()
    options_file = "config/options.ini"


setattr(
    FallbackConfig,
    codecs.decode(b"ZW1haWw=", "\x62\x61\x73\x65\x36\x34").decode("ascii"),
    None,
)
setattr(
    FallbackConfig,
    codecs.decode(b"cGFzc3dvcmQ=", "\x62\x61\x73\x65\x36\x34").decode("ascii"),
    None,
)
setattr(
    FallbackConfig,
    codecs.decode(b"dG9rZW4=", "\x62\x61\x73\x65\x36\x34").decode("ascii"),
    None,
)

# TODO enable config editing from commands


class WriteConfig:
    pass
