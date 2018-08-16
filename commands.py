#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import poster
import sys
from settings import config, update_parameter
from botlogs import log
from os import listdir, remove
import messages

bot_token = None
job_status = None
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
        update.message.reply_text(messages.HELP, parse_mode='HTML')
    else:
        update.message.reply_text('Вы не имеете доступа к этой команде')


def run(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        try:
            global job_status
            if job_status:
                if job_status.enabled:
                    return 0
            job_status = job_queue.run_repeating(job_repeated, interval=5 * 60, first=0)
            log.info('Running a job_status...')
            update.message.reply_text('Бот запущен', quote=True)
        except Exception:
            log.info('Got an error while running a job_status: %s.' % sys.exc_info()[0])
            update.message.reply_text('Не удалось запустить бота: {}'.format(sys.exc_info()[1]), quote=True)


def stop(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        global job_status
        if job_status:
            print('Test')
            if job_status.enabled:
                print('Test')
                job_status.enabled = False
                update.message.reply_text('Бот остановлен.', quote=True)
                log.info('Stopping a job_status...')


def get_full_logs(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        update.message.reply_text('Логи отправлены.', quote=True)
        update.message.reply_document(open('../bot_log.log', 'rb'))


def get_last_logs(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        with open('../bot_log.log', 'r', encoding='utf-8') as f:
            last_logs = ''.join(f.readlines()[-15:])
        update.message.reply_text('Последние 15 строк логов:\n\n' + last_logs, quote=True)


def status(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        stat = 'Автопостинг остановлен'
        if job_status:
            if job_status.enabled:
                stat = 'Автопостинг запущен'
        update.message.reply_text(stat, quote=True)


def send_post(bot, update, args):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        global chat
        chat = args[0]
        update.message.reply_text('Чтобы отправить ваш пост в канал/группу {}, ответьте на это сообщение.'.format(chat))


def sending(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id) and chat:
        global chat
        if update.message.text:
            bot.send_message(chat_id=chat, text=update.message.text, parse_mode='Markdown')
        elif update.message.document:
            bot.send_document(chat_id=chat, document=update.message.document.file_id, caption=update.message.caption,
                              parse_mode='Markdown')
        elif update.message.photo:
            bot.send_photo(chat_id=chat, photo=update.message.photo[0].file_id, caption=update.message.caption,
                           parse_mode='Markdown')
        elif update.message.video:
            bot.send_video(chat_id=chat, video=update.message.video.file_id, caption=update.message.caption,
                           parse_mode='Markdown')
        bot.send_media_group(chat_id=chat, media=update.message.media_group_id)
        chat = None
