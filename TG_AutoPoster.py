#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import configparser
import os.path
from datetime import timedelta
from parser import get_posts
from tempfile import TemporaryDirectory
from time import sleep

from loguru import logger as log
from telegram import Bot
from telegram.utils.request import Request
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
    def __init__(self, config_path=CONFIG_PATH, cache_dir=CACHE_DIR.name):
        self.cache_dir = cache_dir
        self.config_path = config_path
        # Чтение конфигурации бота из файла config.ini
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)
        # Инициализация Telegram бота
        bot_token = self.config.get("global", "bot_token")
        # Указан ли прокси в конфиге
        if self.config.get("global", "proxy_url"):
            log.warning("Бот будет работать через прокси. Возможны перебои в работе бота.")
            request = Request(proxy_url=self.config.get("global", "proxy_url"), connect_timeout=15.0, read_timeout=15.0)
        else:
            request = None
        self.bot = Bot(bot_token, request=request)
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
        self.session = VkApi(
            login=vk_login, password=vk_pass, auth_handler=auth_handler, captcha_handler=captcha_handler
        )
        self.session.auth()
        self.api_vk = self.session.get_api()

    def get_updates(self):
        # Переход в папку с кэшем
        os.chdir(self.cache_dir)
        for group in self.config.sections()[1:]:
            last_id = self.config.getint(group, "last_id", fallback=0)
            pinned_id = self.config.getint(group, "pinned_id", fallback=0)
            disable_notification = self.config.getboolean(
                group,
                "disable_notification",
                fallback=self.config.get("global", "disable_notification", fallback=False),
            )
            # channel = config.get(group, 'channel', fallback=config.get('global', 'admin'))
            # Получение постов
            posts = get_posts(group, last_id, pinned_id, self.api_vk, self.config, self.session)
            for post in posts:
                skip_post = False
                for word in self.stop_list:
                    if word.lower() in post.text.lower():
                        skip_post = True  # Если пост содержит стоп-слово, то пропускаем его.
                        log.info("Пост содержит стоп-слово, поэтому он не будет отправлен.")
                # Отправка постов
                if not skip_post:
                    sender = PostSender(self.bot, post, self.config.get(group, "channel"), disable_notification)
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

    def _save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            self.config.write(f)


if __name__ == "__main__":
    log.info("Начало работы.")
    args = create_parser().parse_args()
    autoposter = AutoPoster(config_path=args.config, cache_dir=args.cache_dir)
    if args.loop or args.sleep:
        sleep_time = args.sleep if args.sleep else 3600
        log.info("Программе был передан аргумен --loop (-l). Запуск бота в бесконечном цикле.")
        autoposter.get_infinity_updates(interval=sleep_time)
    else:
        autoposter.get_updates()
    log.info("Работа завершена. Выход...")
