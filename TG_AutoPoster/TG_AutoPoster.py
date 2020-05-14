#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import configparser
import os.path
from TG_AutoPoster.parsers import get_new_posts, get_new_stories
from tempfile import TemporaryDirectory
from time import sleep

from loguru import logger as log
from pyrogram import Client
from vk_api import VkApi

from TG_AutoPoster.handlers import auth_handler, captcha_handler
from TG_AutoPoster.sender import PostSender

if os.name != "nt":
    TEMP_DIR = TemporaryDirectory(prefix="TG_AutoPoster")
    CACHE_DIR = TEMP_DIR.name
else:
    CACHE_DIR = os.path.join(os.getcwd(), ".cache")
CONFIG_PATH = os.path.join(os.getcwd(), "config.ini")

log.remove()
log.add("./logs/bot_log_{time}.log")


def create_parser():
    parser = argparse.ArgumentParser(
        prog="TG_AutoPoster",
        description="Telegram Bot for AutoPosting from VK",
        epilog="(C) 2018-2020 Adrian Polyakov\nReleased under the MIT License.",
    )

    parser.add_argument(
        "-6", "--ipv6", action="store_true", help="Использовать IPv6 при подключении к Telegram (IPv4 по умолчанию)"
    )
    parser.add_argument(
        "-l",
        "--loop",
        action="store_const",
        const=True,
        default=False,
        help="Запустить бота в бесконечном цикле с проверкой постов раз в час (по умолчанию)",
    )
    parser.add_argument("-s", "--sleep", type=int, default=0, help="Проверять новые посты каждые N секунд", metavar="N")
    parser.add_argument(
        "-c",
        "--config",
        default=CONFIG_PATH,
        help="Абсолютный путь к конфиг файлу бота (по умолчанию {})".format(CONFIG_PATH),
    )
    parser.add_argument(
        "--cache-dir",
        default=CACHE_DIR,
        help="Абсолютный путь к папке с кэшем бота (по умолчанию используется временная папка; .cache в Windows)",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Режим отладки")
    return parser


class AutoPoster:
    def __init__(self, config_path=CONFIG_PATH, cache_dir=CACHE_DIR, ipv6=False):
        self.cache_dir = cache_dir
        self.config_path = config_path
        # Чтение конфигурации бота из файла config.ini
        self._reload_config()
        # Инициализация Telegram бота
        self.bot = Client("TG_AutoPoster", ipv6=ipv6, config_file=config_path, workdir=os.getcwd())
        self.bot.set_parse_mode("html")
        # Чтение из конфига логина, пароля, а также токена (если он есть)
        vk_login = self.config.get("global", "login")
        vk_pass = self.config.get("global", "pass")
        vk_token = self.config.get("global", "token", fallback="")
        # Чтение из конфига пути к файлу со стоп-словами
        self.stop_list = self.config.get("global", "stop_list", fallback=[])
        if self.stop_list:
            # Инициализация списка стоп-слов
            with open(self.stop_list, "r", encoding="utf-8") as f:
                self.stop_list = [i.strip() for i in f.readlines()]
            log.info("Загружен список стоп-слов")
        # Инициализация ВК сессии
        if vk_token:  # Если в конфиге был указан токен, то используем его
            self.vk_session = VkApi(token=vk_token)  # При использовании токена будут недоступны аудиозаписи
        else:  # В противном случае авторизуемся, используя логин и пароль
            self.vk_session = VkApi(
                login=vk_login, password=vk_pass, auth_handler=auth_handler, captcha_handler=captcha_handler
            )
            self.vk_session.auth()

    def run(self):
        # Переход в папку с кэшем
        try:
            os.chdir(self.cache_dir)
        except FileNotFoundError:
            os.mkdir(self.cache_dir)
        groups = self.config.sections()[3:] if self.config.has_section("proxy") else self.config.sections()[2:]
        for group in groups:
            try:
                chat_id = self.config.getint(group, "channel")
            except ValueError:
                chat_id = self.config.get(group, "channel")
            disable_notification = self.config.getboolean(
                group,
                "disable_notification",
                fallback=self.config.getboolean("global", "disable_notification", fallback=False),
            )
            disable_web_page_preview = self.config.getboolean(
                group,
                "disable_web_page_preview",
                fallback=self.config.getboolean("global", "disable_web_page_preview", fallback=True),
            )
            send_stories = self.config.getboolean(
                group, "send_stories", fallback=self.config.getboolean("global", "send_stories", fallback=False)
            )
            # Получение постов
            posts = get_new_posts(group, self.vk_session, self.config)
            for post in posts:
                skip_post = False
                for word in self.stop_list:
                    if word.lower() in post.text.lower():
                        skip_post = True  # Если пост содержит стоп-слово, то пропускаем его.
                        log.info("Пост содержит стоп-слово, поэтому он не будет отправлен.")
                # Отправка постов
                if not skip_post:
                    with self.bot:
                        sender = PostSender(self.bot, post, chat_id, disable_notification, disable_web_page_preview)
                        sender.send_post()
                self._save_config()
            if send_stories:
                # Получение историй, если включено
                stories = get_new_stories(group, self.vk_session, self.config)
                for story in stories:
                    with self.bot:
                        sender = PostSender(
                            self.bot,
                            story,
                            self.config.get(group, "channel"),
                            disable_notification,
                            disable_web_page_preview,
                        )
                        sender.send_post()
                    self._save_config()
            for data in os.listdir(self.cache_dir):
                os.remove(os.path.join(self.cache_dir, data))
        self._save_config()

    def infinity_run(self, interval=3600):
        while True:
            self.run()
            log.info("Работа завершена. Отправка в сон на {} секунд.", interval)
            sleep(interval)
            self._reload_config()

    def _save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            self.config.write(f)
        log.debug("Config saved.")

    def _reload_config(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)
        log.debug("Config reloaded.")

