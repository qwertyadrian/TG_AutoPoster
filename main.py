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
from botlogs import log


if __name__ == '__main__':
    bot = Bot(config.get('global', 'bot_token'))
    if config.get('global', 'proxy_url'):
        log.warning('[TG] Настройка прокси. Это отрицально влияет на работу бота')
        api._pools = {'default': ProxyManager(proxy_url=config.get('global', 'proxy_url'), num_pools=3, maxsize=10,
                                              retries=False, timeout=30)}
        api._onetime_pool_spec = (ProxyManager, dict(proxy_url=config.get('global', 'proxy_url'), num_pools=1,
                                                     maxsize=1, retries=False, timeout=30))
    while True:
        for group in config.sections()[1:]:
            poster.updater(bot, group, config.getint(group, 'last_id'))
        for data in listdir('.'):
            log.info('Очистка кэша')
            remove(data)
        if config.getboolean('global', 'single_run'):
            log.info('Выход')
            break
        log.info('Переход в режим сна')
        sleep(5*60)
