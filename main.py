#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from os import mkdir, chdir

try:
    mkdir('data')
    chdir('data')
except FileExistsError:
    chdir('data')

from telegram.ext import *
from settings import config
import commands
from botlogs import log


def error(bot, update, error):
    log.warning('[TG] Update "%s" caused error "%s"' % (update, error))


def set_starter_settings():
    commands.bot_token = config.get('global', 'bot_token')
    commands.job_queue = job_queue
    commands.job = job


if __name__ == '__main__':

    def update(request_kwargs=None):
        global updater, dp, job_queue, job
        updater = Updater(config.get('global', 'bot_token'), request_kwargs=request_kwargs)
        dp = updater.dispatcher
        job_queue = updater.job_queue
        dp.add_handler(CommandHandler('start', commands.start))
        dp.add_handler(CommandHandler('help', commands.help))
        dp.add_handler(CommandHandler('run', commands.run))
        dp.add_handler(CommandHandler('stop', commands.stop))
        dp.add_handler(CommandHandler('get_full_logs', commands.get_full_logs))
        dp.add_handler(CommandHandler('get_last_logs', commands.get_last_logs))
        dp.add_handler(CommandHandler('status', commands.status))
        dp.add_handler(MessageHandler(callback=commands.is_admin, filters=Filters.regex(config.get('global', 'bot_token'))), group=1)
        dp.add_handler(CommandHandler('send_post', commands.send_post))
        dp.add_handler(MessageHandler(callback=commands.sending, filters=Filters.reply))
        job = job_queue.run_repeating(commands.job_repeated, interval=5 * 60, first=0)


    if config.get('global', 'proxy_url'):
        REQUEST_KWARGS = {'proxy_url': config.get('global', 'proxy_url'), 'connect_timeout': 15.0, 'read_timeout': 15.0}
        update(REQUEST_KWARGS)
    else:
        update()

    set_starter_settings()
    dp.add_error_handler(error)
    # noinspection PyBroadException
    try:
        updater.start_polling()
        updater.idle()
    except Exception:
        log.warning('Critical error occured: {0} {1}. Please restart a bot.'.format(sys.exc_info()[0], sys.exc_info()[1]))
