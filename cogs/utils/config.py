import logging
import os
import shutil
from configparser import SafeConfigParser

log = logging.getLogger(__name__)


class Config:
    def __init__(self):
        config = SafeConfigParser(interpolation=None)
        if not os.path.exists('config/options.ini'):
            shutil.copyfile('config/example_options.ini', 'config/options.ini')

        config.read('config/options.ini', encoding='utf-8')
        confsections = {'Credentials',
                        'IDs',
                        'Bot',
                        'etc'}.difference(config.sections())

        if confsections:
            raise Exception(
                log.error('Config sections altered!\n'
                          'Make sure you have a correctly formatted config!'))

        self.login_token = config.get('Credentials', 'Token')

        self.owner_id = config.get('IDs', 'OwnerID')
        self.dev_ids = config.get('IDs', 'DevIDs')
        self.mod_ids = config.get('IDs', 'ModIDs')

        self.command_prefix = config.get('Bot', 'CommandPrefix')

