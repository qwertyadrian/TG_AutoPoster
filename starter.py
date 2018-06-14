#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import poster
from settings import config, update_parameter
from botlogs import log
from os import listdir, remove
import messages


def starter(bot):
    for group in config.sections()[1:]:
        poster.updater(bot, group, config.getint(group, 'last_id'))
    log.info('Очистка кэша')
    for data in listdir('.'):
        remove(data)
    log.info('Переход в режим сна')


def start(bot, update):
    update.message.reply_text('Для доступа к командам управления ботом отправьте его токен.')


def is_admin(bot, update):
    if update.message.text == config.get('global', 'bot_token'):
        if config.get('global', 'admin') != update.message.from_user.id:
            update_parameter('global', 'admin', update.message.from_user.id)
            log.info('[TG] Установлен администратор бота с ID {0}'.format(update.message.from_user.id))
            update.message.reply_text('Доступ получен.\n\nКоманда просмотра всех доступных команд: /help')


def help(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        update.message.reply_text(messages.HELP, parse_mode='Markdown')
