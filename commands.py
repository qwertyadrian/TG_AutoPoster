#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
import poster
import sys
from settings import config, update_parameter, remove_section, add_section
from botlogs import log
from os import listdir, remove
from random import choice
import messages
from classes import build_menu

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
            if job_status.enabled:
                job_status.enabled = False
                update.message.reply_text('Бот остановлен.', quote=True)
                log.info('Stopping a job_status...')


def get_full_logs(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        update.message.reply_text('Логи отправлены.', quote=True)
        update.message.reply_document(open('../bot_log.log', 'rb'))


def get_last_logs(bot, update, args):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        if args:
            string = int(args[0])
        else:
            string = 15
        with open('../bot_log.log', 'r', encoding='utf-8') as f:
            last_logs = ''.join(f.readlines()[-string:])
        update.message.reply_text('Последние {} строк логов:\n\n'.format(str(string)) + last_logs, quote=True)


def status(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        stat = 'Автопостинг остановлен'
        if job_status:
            if job_status.enabled:
                stat = 'Автопостинг запущен'
        update.message.reply_text(stat, quote=True)


def send_post(bot, update, args):
    global chat
    if len(args) != 0:
        chat = args[0]
    else:
        chat = config.get('global', 'main_group')
    update.message.reply_text('Чтобы отправить ваш пост в канал/группу {}, ответьте на это сообщение.'.format(chat),
                              reply_markup=ForceReply())


def sending(bot, update):
    global chat, message
    if str(config.get('global', 'admin')) == str(update.message.from_user.id) and chat:
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
    else:
        button_list = [InlineKeyboardButton('Принять', callback_data="3"), InlineKeyboardButton('Отклонить', callback_data="4")]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
        message = bot.forward_message(chat_id=config.get('global', 'admin'), from_chat_id=update.message.chat.id,
                                      message_id=update.message.message_id)
        bot.send_message(chat_id=config.get('global', 'admin'), text='Что сделать с сообщением выше?', reply_markup=reply_markup)


def source_list(bot, update):
    sources_list = config.sections()[1:]
    sources = 'Список источников:\nИсточник        ---->        Назначение  (ID последнего отправленного поста)\n\n'
    for source in sources_list:
        sources += 'https://vk.com/{}        ---->        {}  ({})\n'.format(source, config.get(source, 'channel'),
                                                                             config.get(source, 'last_id'))
    sources += '\nДля удаления источника отправьте команду /remove <домен группы вк>\nНапример, /remove ' +\
               choice(sources_list)
    update.message.reply_text(sources, disable_web_page_preview=True)


def remove_source(bot, update, args):
    if args:
        section = remove_section(args[0])
        info = 'Источник {0[0]} был удален.\nДля его восстановления используйте команду' \
               ' <code>/add {0[0]} {0[1]} {0[2]}</code>'.format(section)
        update.message.reply_text(info, parse_mode='HTML')
    else:
        update.message.reply_text(messages.REMOVE, parse_mode='Markdown')


def add_source(bot, update, args):
    if args:
        section = add_section(*args)
        info = 'Источник {0[0]} был добавлен.'.format(section)
        update.message.reply_text(info)
    else:
        update.message.reply_text(messages.ADD, parse_mode='Markdown')


def button(bot, update):
    # TODO Доделать управление источниками через меню
    query = update.callback_query
    if query.data == '3':
        bot.forward_message(chat_id=config.get('global', 'main_group'), from_chat_id=message.chat.id,
                            message_id=message.message_id)
        bot.edit_message_text(text='Принято', chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
    elif query.data == '4':
        bot.edit_message_text(text='Отклонено', chat_id=query.message.chat_id,
                              message_id=query.message.message_id)


def get_id(bot, update):
    # Get group or user ID
    update.message.reply_text('Group ID: {0}'.format(update.message.chat.id))


def get_config(bot, update):
    if str(config.get('global', 'admin')) == str(update.message.from_user.id):
        update.message.reply_text('Конфигурация бота:\n ```{}```'.format(open('../config.ini').read()),
                                  quote=True, parse_mode='Markdown')
        update.message.reply_document(open('../config.ini', 'rb'), caption='Файл конфигурации бота.')
