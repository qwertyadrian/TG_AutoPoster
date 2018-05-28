#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from os import mkdir, chdir, listdir, remove

try:
    mkdir('data')
    chdir('data')
except FileExistsError:
    chdir('data')

import poster
from time import sleep
from telepot import Bot, api
from settings import config
from urllib3 import ProxyManager


if __name__ == '__main__':
    bot = Bot(config.get('global', 'bot_token'))
    proxy_url = "https://176.123.230.146:3128"  # Переменная с HTTPS прокси
    api._pools = {'default': ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30)}
    api._onetime_pool_spec = (ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))
    if config.getboolean('global', 'single_run'):
        for group in config.sections()[1:]:
            poster.updater(bot, config.get(group, 'domain'), config.getint(group, 'last_id'))
        for data in listdir('.'):
            remove(data)
    else:
        while True:
            for group in config.sections()[1:]:
                poster.updater(bot, config.get(group, 'domain'), config.getint(group, 'last_id'))
            for data in listdir('.'):
                remove(data)
            sleep(5*60)

