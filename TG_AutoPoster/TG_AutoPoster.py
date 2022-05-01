#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import configparser
import os
from pathlib import Path
from re import sub
from tempfile import TemporaryDirectory
from time import sleep

from loguru import logger as log
from pyrogram import Client
from pyrogram.enums import ParseMode
from vk_api import VkApi

from .handlers import auth_handler, captcha_handler
from .group import Group
from .sender import PostSender

if os.name != "nt":
    TEMP_DIR = TemporaryDirectory(prefix="TG_AutoPoster")
    CACHE_DIR = Path(TEMP_DIR.name)
else:
    CACHE_DIR = Path.cwd() / ".cache"
CONFIG_PATH = Path.cwd() / "config.ini"


def create_parser():
    parser = argparse.ArgumentParser(
        prog="TG_AutoPoster",
        description="Telegram Bot for AutoPosting from VK",
        epilog="(C) 2018-2022 Adrian Polyakov\nReleased under the MIT License.",
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
        self.cache_dir = Path(cache_dir).absolute()
        self.config_path = Path(config_path).absolute()
        # Чтение конфигурации бота из файла config.ini
        self._reload_config()
        if self.config.getboolean("proxy", "enabled", fallback=None):
            proxy = dict(
                scheme="socks5",
                hostname=self.config.get("proxy", "hostname"),
                port=self.config.getint("proxy", "port"),
            )
            username = self.config.get("proxy", "username")
            password = self.config.get("proxy", "password")
            if username and password:
                proxy["username"] = username
                proxy["password"] = password
        else:
            proxy = None
        # Инициализация Telegram бота
        self.bot = Client(
            name="TG_AutoPoster",
            api_id=self.config.getint("pyrogram", "api_id"),
            api_hash=self.config.get("pyrogram", "api_hash"),
            bot_token=self.config.get("pyrogram", "bot_token"),
            proxy=proxy,
            ipv6=ipv6,
            workdir=str(Path.cwd()),
        )
        self.bot.set_parse_mode(ParseMode.HTML)
        # Чтение из конфига логина, пароля, а также токена (если он есть)
        vk_login = self.config.get("global", "login")
        vk_pass = self.config.get("global", "pass")
        vk_token = self.config.get("global", "token", fallback="")
        # Чтение из конфига пути к файлу со стоп-словами
        self.stop_list = Path(self.config.get("global", "stop_list", fallback="")).absolute()
        self.blacklist = Path(self.config.get("global", "blacklist", fallback="")).absolute()

        if self.stop_list.is_file():
            # Инициализация списка стоп-слов
            self.stop_list = self.stop_list.read_text().split("\n")
            log.info("Загружен список стоп-слов")
        else:
            self.stop_list = []

        if self.blacklist.is_file():
            self.blacklist = self.blacklist.read_text().split("\n")
            log.info("Загружен черный спиок слов")
        else:
            self.blacklist = []

        # Инициализация ВК сессии
        if vk_token:  # Если в конфиге был указан токен, то используем его
            self.vk_session = VkApi(token=vk_token, api_version="5.131")
        else:  # В противном случае авторизуемся, используя логин и пароль
            log.critical("Использование логина и пароля не рекомендуется. "
                         "Используйте ключ доступа пользователя.")
            self.vk_session = VkApi(
                login=vk_login,
                password=vk_pass,
                auth_handler=auth_handler,
                captcha_handler=captcha_handler,
                api_version="5.131",
            )
            self.vk_session.auth()

    def run(self):
        # Переход в папку с кэшем
        try:
            os.chdir(self.cache_dir)
        except FileNotFoundError:
            self.cache_dir.mkdir()
        domains = self.config.sections()[3:] if self.config.has_section("proxy") else self.config.sections()[2:]
        for domain in domains:
            chat_ids = self.config.get(domain, "channel").split()
            disable_notification = self.config.getboolean(
                domain,
                "disable_notification",
                fallback=self.config.getboolean("global", "disable_notification", fallback=False),
            )
            disable_web_page_preview = self.config.getboolean(
                domain,
                "disable_web_page_preview",
                fallback=self.config.getboolean("global", "disable_web_page_preview", fallback=True),
            )
            send_stories = self.config.getboolean(
                domain, "send_stories", fallback=self.config.getboolean("global", "send_stories", fallback=False)
            )
            last_id = self.config.getint(domain, "last_id", fallback=0)
            pinned_id = self.config.getint(domain, "pinned_id", fallback=0)
            send_reposts = self.config.get(
                domain, "send_reposts", fallback=self.config.get("global", "send_reposts", fallback=0)
            )
            sign_posts = self.config.getboolean(
                domain, "sign_posts", fallback=self.config.getboolean("global", "sign_posts", fallback=True)
            )
            what_to_parse = set(
                self.config.get(
                    domain, "what_to_send", fallback=self.config.get("global", "what_to_send", fallback="all")
                ).split(",")
            )
            posts_count = self.config.getint(
                domain, "posts_count", fallback=self.config.get("global", "posts_count", fallback=11)
            )
            last_story_id = self.config.getint(domain, "last_story_id", fallback=0)
            group = Group(
                domain,
                self.vk_session,
                last_id,
                pinned_id,
                send_reposts,
                sign_posts,
                what_to_parse,
                posts_count,
                last_story_id,
            )
            # Получение постов
            posts = group.get_posts()
            for post in posts:
                skip_post = False
                for word in self.stop_list:
                    if word.lower() in post.text.lower():
                        skip_post = True  # Если пост содержит стоп-слово, то пропускаем его.
                        log.info("Пост содержит стоп-слово, поэтому он не будет отправлен.")
                # Отправка постов
                if not skip_post:
                    for word in self.blacklist:
                        post.text = sub(word, "", post.text)
                    with self.bot:
                        for chat_id in chat_ids:
                            chat_id = int(chat_id) if chat_id.startswith("-") or chat_id.isnumeric() else chat_id
                            sender = PostSender(self.bot, post, chat_id, disable_notification, disable_web_page_preview)
                            sender.send_post()
                self.config.set(domain, "pinned_id", str(group.pinned_id))
                self.config.set(domain, "last_id", str(group.last_id))
                self._save_config()
            if send_stories:
                # Получение историй, если включено
                stories = group.get_stories()
                for story in stories:
                    with self.bot:
                        for chat_id in chat_ids:
                            chat_id = int(chat_id) if chat_id.startswith("-") or chat_id.isnumeric() else chat_id
                            sender = PostSender(
                                self.bot,
                                story,
                                chat_id,
                                disable_notification,
                                disable_web_page_preview,
                            )
                            sender.send_post()
                        self.config.set(domain, "last_story_id", str(group.last_story_id))
                    self._save_config()
            log.debug("Clearing cache directory {}", self.cache_dir)
            for data in self.cache_dir.iterdir():
                data.unlink()
        self._save_config()

    def infinity_run(self, interval=3600):
        errors = 0
        while True:
            try:
                self.run()
            except Exception:
                log.opt(exception=True).exception("При работе программы возникла ошибка")
                if errors >= 10:
                    log.error("Ошибка возникла более 10 раз подряд. Выход...")
                    exit(1)
                errors += 1
            else:
                errors = 0
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
