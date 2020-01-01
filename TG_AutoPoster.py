#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram import Bot
from telegram.utils.request import Request
from vk_api import VkApi
from handlers import *
from parser import get_posts
from sender import PostSender
from os import chdir, listdir, remove, mkdir
from loguru import logger as log
from datetime import timedelta
from time import sleep
import configparser
import argparse


def create_parser():
    parser = argparse.ArgumentParser(prog='TG_AutoPoster',
                                     description='Telegram Bot for AutoPosting from VK',
                                     epilog='(C) 2018-2020 Adrian Polyakov\nReleased under the MIT License.')

    parser.add_argument('-l', '--loop', action='store_const', const=True,
                        help='Запустить бота в бесконечном цикле с проверкой постов раз в час (по умолчанию)')
    parser.add_argument('-s', '--sleep', type=int, default=0,
                        help='Проверять новые посты каждые N секунд)', metavar='N')
    parser.add_argument('-c', '--config', default='config.ini',
                        help='Путь к конфиг файлу бота (по умолчанию ./config.ini)')
    return parser


cache_directory = '.cache'
config = None
bot = None
stop_list = None
api_vk = None
session = None
log.add('./logs/bot_log_{time}.log', retention=timedelta(days=2))


def init(config_path='config.ini'):
    global config, bot, stop_list, api_vk, session
    # Чтение конфигурации бота из файла config.ini
    config = configparser.ConfigParser()
    config.read(config_path)
    # Инициализация Telegram бота
    bot_token = config.get('global', 'bot_token')
    # Указан ли прокси в конфиге
    if config.get('global', 'proxy_url'):
        log.warning('Бот будет работать через прокси. Возможны перебои в работе бота.')
        request = Request(proxy_url=config.get('global', 'proxy_url'), connect_timeout=15.0, read_timeout=15.0)
    else:
        request = None
    bot = Bot(bot_token, request=request)
    # Чтение из конфига логина и пароля ВК
    vk_login = config.get('global', 'login')
    vk_pass = config.get('global', 'pass')
    # Чтение из конфига пути к файлу со стоп-словами
    stop_list = config.get('global', 'stop_list', fallback=[])
    if stop_list:
        # Инициализация списка стоп-слов
        with open(stop_list, 'r', encoding='utf-8') as f:
            stop_list = [i.strip() for i in f.readlines()]
    # Инициализация ВК сессии
    session = VkApi(login=vk_login, password=vk_pass, auth_handler=auth_handler, captcha_handler=captcha_handler)
    session.auth()
    api_vk = session.get_api()


@log.catch(reraise=True)
def main(config_path='../config.ini'):
    # Переход в папку с кэшем
    try:
        chdir(cache_directory)
    except FileNotFoundError:
        log.exception('Директории кэша не существует. Создание...')
        mkdir(cache_directory)
        chdir(cache_directory)
    for group in config.sections()[1:]:
        last_id = config.getint(group, 'last_id', fallback=0)
        pinned_id = config.getint(group, 'pinned_id', fallback=0)
        # channel = config.get(group, 'channel', fallback=config.get('global', 'admin'))
        # Получение постов
        a = get_posts(group, last_id, pinned_id, api_vk, config, session, config_path)
        for post in a:
            skip_post = False
            for word in stop_list:
                if word.lower() in post.text.lower():
                    skip_post = True  # Если пост содержит стоп-слово, то пропускаем его.
                    log.info('Пост содержит стоп-слово, поэтому он не будет отправлен.')
            # Отправка постов
            if not skip_post:
                sender = PostSender(bot, post, config.get(group, 'channel'))
                sender.send_post()
    for data in listdir('.'):
        remove(data)
    chdir('../')


if __name__ == '__main__':
    log.info('Начало работы.')
    cmd_parser = create_parser()
    namespace = cmd_parser.parse_args()
    if namespace.loop or namespace.sleep:
        sleep_time = namespace.sleep if namespace.sleep else 3600
        log.info('Программе был передан аргумен --loop (-l). Запуск бота в бесконечном цикле.')
        while True:
            init(config_path=namespace.config)
            main()
            log.info('Работа завершена. Отправка в сон на {} секунд.'.format(sleep_time))
            sleep(sleep_time)
    else:
        init(config_path=namespace.config)
        main()
    log.info('Работа завершена. Выход...')
