#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import poster
import sys
from settings import config, update_parameter
from botlogs import log
from os import listdir, remove
import messages

bot_token = None
job = None
job_queue = None


def job_repeated(bot, job):
    starter(bot)


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
    else:
        update.message.reply_text('Вы не имеете доступа к этой команде')


def run(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        try:
            global job
            if job:
                if job.enabled:
                    return 0
            job = job_queue.run_repeating(job_repeated, interval=5 * 60, first=0)
            log.info('Running a job...')
            update.message.reply_text('Бот запущен')
        except Exception:
            log.info('Got an error while running a job: %s.' % sys.exc_info()[0])
            update.message.reply_text('Не удалось запустить бота: {}'.format(sys.exc_info()[1]))


def stop(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        global job
        if job:
            print('Test')
            if job.enabled:
                print('Test')
                job.enabled = False
                update.message.reply_text('Бот остановлен.')
                log.info('Stopping a job...')
