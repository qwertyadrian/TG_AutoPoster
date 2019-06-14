#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram import Bot
from vk_api import VkApi
from handlers import *
from parser import get_posts
from sender import PostSender
from os import chdir, listdir, remove
import configparser


# Чтение конфигурации бота из файла config.ini
config = configparser.ConfigParser()
config.read_file(open('./config.ini', 'r', encoding='utf-8'))
# Инициализация Telegram бота
bot_token = config.get('global', 'bot_token')
bot = Bot(bot_token)
# Чтение из конфига логина и пароля ВК
vk_login = config.get('global', 'login')
vk_pass = config.get('global', 'pass')
# Инициализация ВК сессии
session = VkApi(login=vk_login, password=vk_pass, auth_handler=auth_handler,
                captcha_handler=captcha_handler)
session.auth()
api_vk = session.get_api()
# print(api_vk)

chdir('data')
for group in config.sections()[1:]:
    a = get_posts(group, config.getint(group, 'last_id'), api_vk, config, session)
    for post in a:
        sender = PostSender(bot, post, config.get(group, 'channel'))
        sender.send_post()
for data in listdir('.'):
    remove(data)
chdir('../')



