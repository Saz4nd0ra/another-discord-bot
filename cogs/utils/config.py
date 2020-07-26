import logging
import os
import shutil
from configparser import SafeConfigParser

log = logging.getLogger(__name__)


#TODO maybe add a fallback, in case the user forgets to set a setting
class Config:
    def __init__(self):
        config = SafeConfigParser(interpolation=None)
        if not os.path.exists('config/options.ini'):
            shutil.copyfile('config/example_options.ini', 'config/options.ini')

        config.read('config/options.ini', encoding='utf-8')
        confsections = {'Credentials',
                        'IDs',
                        'Bot',
                        'Music',
                        'etc'}.difference(config.sections())

        if confsections:
            raise Exception(
                log.error('Config sections altered!\n'
                          'Make sure you have a correctly formatted config!'))

        self.login_token = config.get('Credentials', 'Token')

        # TODO check if the ids are correct, for later checks and so on
        self.dev_ids = config.get('IDs', 'DevIDs')

        self.command_prefix = config.get('Bot', 'CommandPrefix')
        self.wh_id = config.get('Bot', 'WebhookID')
        self.wh_token = config.get('Bot', 'WebhookToken')

        self.vote_skip = config.get('Music', 'VoteSkip')
        self.skip_ratio = config.get('Music', 'SkipRatio')


# this will be a fallback config soon
class Fallback:
    pass
