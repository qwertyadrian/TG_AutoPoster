#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import configparser
import os.path
from datetime import timedelta
from parser import get_new_posts, get_new_stories
from tempfile import TemporaryDirectory
from time import sleep

from loguru import logger as log
from pyrogram import Client
from vk_api import VkApi

from handlers import auth_handler, captcha_handler
from sender import PostSender

CACHE_DIR = TemporaryDirectory(prefix="TG_AutoPoster")
CONFIG_PATH = os.path.join(os.getcwd(), "config.ini")

log.add("./logs/bot_log_{time}.log", retention=timedelta(days=2))


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
        default=CACHE_DIR.name,
        help="Абсолютный путь к папке с кэшем бота (по умолчанию используется временная папка)",
    )
    return parser


class AutoPoster:
    def __init__(self, config_path=CONFIG_PATH, cache_dir=CACHE_DIR.name, ipv6=False):
        self.cache_dir = cache_dir
        self.config_path = config_path
        # Чтение конфигурации бота из файла config.ini
        self._reload_config()
        # Инициализация Telegram бота
        self.bot = Client("TG_AutoPoster", ipv6=ipv6, config_file=config_path)
        self.bot.set_parse_mode("html")
        # Чтение из конфига логина и пароля ВК
        vk_login = self.config.get("global", "login")
        vk_pass = self.config.get("global", "pass")
        # Чтение из конфига пути к файлу со стоп-словами
        self.stop_list = self.config.get("global", "stop_list", fallback=[])
        if self.stop_list:
            # Инициализация списка стоп-слов
            with open(self.stop_list, "r", encoding="utf-8") as f:
                self.stop_list = [i.strip() for i in f.readlines()]
        # Инициализация ВК сессии
        self.vk_session = VkApi(
            login=vk_login, password=vk_pass, auth_handler=auth_handler, captcha_handler=captcha_handler
        )
        self.vk_session.auth()

    def get_updates(self):
        # Переход в папку с кэшем
        os.chdir(self.cache_dir)
        groups = self.config.sections()[3:] if self.config.has_section("proxy") else self.config.sections()[2:]
        for group in groups:
            try:
                chat_id = self.config.getint(group, "channel")
            except ValueError:
                chat_id = self.config.get(group, "channel")
            disable_notification = self.config.getboolean(
                group,
                "disable_notification",
                fallback=self.config.get("global", "disable_notification", fallback=False),
            )
            send_stories = self.config.getboolean(
                group, "send_stories", fallback=self.config.get("global", "send_stories", fallback=False)
            )
            # channel = config.get(group, 'channel', fallback=config.get('global', 'admin'))
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
                        sender = PostSender(self.bot, post, chat_id, disable_notification)
                        sender.send_post()
                self._save_config()
            if send_stories:
                # Получение историй, если включено
                last_story_id = self.config.getint(group, "last_story_id", fallback=0)
                stories = get_new_stories(group, last_story_id, self.vk_session, self.config)
                for story in stories:
                    with self.bot:
                        sender = PostSender(self.bot, story, self.config.get(group, "channel"), disable_notification)
                        sender.send_post()
                    self._save_config()
            for data in os.listdir("."):
                os.remove(data)
        self._save_config()

    def get_infinity_updates(self, interval=3600):
        while True:
            self.get_updates()
            log.info("Работа завершена. Отправка в сон на {} секунд.".format(interval))
            sleep(interval)
            self._reload_config()

    def _save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            self.config.write(f)

    def _reload_config(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)


if __name__ == "__main__":
    log.info("Начало работы.")
    args = create_parser().parse_args()
    autoposter = AutoPoster(config_path=args.config, cache_dir=args.cache_dir, ipv6=args.ipv6)
    if args.loop or args.sleep:
        sleep_time = args.sleep if args.sleep else 3600
        log.info("Программе был передан аргумен --loop (-l). Запуск бота в бесконечном цикле.")
        autoposter.get_infinity_updates(interval=sleep_time)
    else:
        autoposter.get_updates()
    log.info("Работа завершена. Выход...")
