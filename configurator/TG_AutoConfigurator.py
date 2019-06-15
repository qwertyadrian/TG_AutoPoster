import configparser
import telebot
# import daemon
import commands
from loguru import logger


def main():
    # Чтение конфигурации бота из файла config.ini.example
    config = configparser.ConfigParser()
    config.read_file(open('config.ini', 'r', encoding='utf-8'))
    # Инициализация Telegram бота
    bot_token = config.get('DEFAULT', 'bot_token')
    bot = telebot.TeleBot(bot_token)

    admin_id = config.getint('DEFAULT', 'admin_id')
    bot_config_path = config.get('DEFAULT', 'bot_config_path')
    bot_logs_folder_path = config.get('DEFAULT', 'bot_logs_folder_path')

    commands.setup(bot, admin_id, bot_config_path, bot_logs_folder_path)

    bot.polling(none_stop=True)


if __name__ == '__main__':
    # with daemon.DaemonContext(working_directory='.'):
    #     logger.add('./logs/bot_log_{time}.log')
    main = logger.catch(main)
    main()
