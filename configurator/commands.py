import messages
from config_tools import remove_section, add_section
from tools import split
from random import choice
import configparser
import os


def setup(bot, admin_id, bot_config_path, bot_logs_folder_path):
    def admin_check(message):
        return message.from_user.id == admin_id

    @bot.message_handler(func=admin_check, commands=['start', 'help'])
    def send_welcome(message):
        bot.reply_to(message, messages.HELP, parse_mode='HTML')

    @bot.message_handler(func=admin_check, commands=['get_full_logs'])
    def send_full_logs(message):
        try:
            logs = os.path.join(bot_logs_folder_path, sorted(os.listdir(bot_logs_folder_path))[-1])
        except (FileNotFoundError, IndexError):
            logs = None
        if logs:
            bot.reply_to(message, 'Логи отправлены.')
            bot.send_document(message.from_user.id, open(logs, 'rb'))
        else:
            bot.reply_to(message, 'Логи не найдены.')

    @bot.message_handler(func=admin_check, commands=['get_last_logs'])
    def send_last_logs(message):
        try:
            logs = os.path.join(bot_logs_folder_path, sorted(os.listdir(bot_logs_folder_path))[-1])
        except (FileNotFoundError, IndexError):
            logs = None
        args = extract_arg(message.text)
        if args:
            lines = int(args[0])
        else:
            lines = 15
        if logs:
            with open(logs, 'r', encoding='utf-8') as f:
                last_logs = ''.join(f.readlines()[-lines:])
                last_logs = 'Последние {} строк логов:\n\n'.format(str(lines)) + last_logs
            for msg in split(last_logs):
                bot.reply_to(message, msg)
        else:
            bot.reply_to(message, 'Логи не найдены.')

    @bot.message_handler(func=admin_check, commands=['list', 'sources_list'])
    def source_list(message):
        config = configparser.ConfigParser()
        config.read_file(open(bot_config_path, 'r', encoding='utf-8'))
        sources_list = config.sections()[1:]
        sources = 'Список источников:\nИсточник        ---->        Назначение  (ID последнего отправленного поста)\n\n'
        for source in sources_list:
            sources += 'https://vk.com/{}        ---->        {}  ({})\n'.format(source, config.get(source, 'channel'),
                                                                                 config.get(source, 'last_id'))
        sources += '\nДля удаления источника отправьте команду /remove <домен группы вк>\nНапример, /remove ' + choice(
            sources_list)
        bot.reply_to(message, sources, disable_web_page_preview=True)

    @bot.message_handler(func=admin_check, commands=['remove_source', 'remove', 'delete', 'delete_source'])
    def remove_source(message):
        args = extract_arg(message.text)
        if args:
            section = remove_section(bot_config_path, args[0])
            info = 'Источник {0[0]} был удален.\nДля его восстановления используйте команду' \
                   ' <code>/add {0[0]} {0[1]} {0[2]}</code>'.format(section)
            bot.reply_to(message, info, parse_mode='HTML')
        else:
            bot.reply_to(message, messages.REMOVE, parse_mode='Markdown')

    @bot.message_handler(func=admin_check, commands=['add'])
    def add_source(message):
        args = extract_arg(message.text)
        if args:
            section = add_section(bot_config_path, *args)
            info = 'Источник {0[0]} был добавлен.'.format(section)
            bot.reply_to(message, info)
        else:
            bot.reply_to(message, messages.ADD, parse_mode='Markdown')

    @bot.message_handler(func=admin_check, commands=['get_config'])
    def get_config(message):
        bot.reply_to(message, 'Конфигурация бота:\n ```{}```'.format(open('../config.ini').read()),
                     parse_mode='Markdown')
        bot.send_document(chat_id=message.from_user.id, data=open(bot_config_path, 'rb'),
                          caption='Файл конфигурации бота.')


def extract_arg(arg):
    return arg.split()[1:]
