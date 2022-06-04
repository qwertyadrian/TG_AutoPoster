import os
from importlib import import_module
from itertools import chain
from pathlib import Path

import yaml
from loguru import logger
from pyrogram import Client
from pyrogram.handlers.handler import Handler
from vk_api import VkApi

from .utils import Group, Sender, auth_handler, captcha_handler, ini_to_dict


class AutoPoster(Client):
    def __init__(
        self,
        config_path: Path = Path("config.yaml"),
        logs_dir: Path = Path("logs"),
        cache_dir: Path = Path(".cache"),
        ipv6: bool = False,
        **kwargs,
    ):
        name = self.__class__.__name__.lower()

        self.config_path = config_path.absolute()
        self.logs_path = logs_dir.absolute()
        self.cache_dir = cache_dir.absolute()

        if self.config_path.exists():
            with self.config_path.open() as stream:
                self.config: dict = yaml.safe_load(stream)
        else:
            self.config = ini_to_dict(self.config_path.with_suffix(".ini"))

        self.admins_id = self.config.get("settings", {}).get("admins_id", [])

        if self.config.get("proxy"):
            proxy = self.config["proxy"]
            proxy["scheme"] = "socks5"
        else:
            proxy = None

        super().__init__(
            name,
            **self.config["telegram"],
            proxy=proxy,
            ipv6=ipv6,
            plugins=dict(
                root="TG_AutoPoster.plugins",
            ),
            **kwargs,
        )

    def load_plugins(self):
        if self.plugins:
            plugins = self.plugins.copy()
            module = import_module(plugins["root"])

            for name in vars(module).keys():
                # noinspection PyBroadException
                try:
                    for handler, group in getattr(module, name).handlers:
                        if isinstance(handler, Handler) and isinstance(group, int):
                            self.add_handler(handler, group)
                except Exception:
                    pass

    def get_new_posts(self):
        try:
            os.chdir(self.cache_dir)
        except FileNotFoundError:
            self.cache_dir.mkdir()
            os.chdir(self.cache_dir)

        if self.config["vk"].get("token"):
            vk_session = VkApi(token=self.config["vk"]["token"], api_version="5.131")
        else:
            logger.warning(
                "Использование логина и пароля не рекомендуется. "
                "Используйте ключ доступа пользователя."
            )
            vk_session = VkApi(
                login=self.config["vk"]["login"],
                password=self.config["vk"]["password"],
                auth_handler=auth_handler,
                captcha_handler=captcha_handler,
                api_version="5.131",
            )
        for domain in self.config["domains"].keys():
            settings = {
                **self.config.get("settings", {}),
                **self.config["domains"][domain],
            }
            group = Group(
                domain=domain,
                session=vk_session,
                **settings,
            )
            chat_ids = self.config["domains"][domain]["channel"]
            for post in chain(group.get_posts(), group.get_stories()):
                if post:
                    sender = Sender(
                        bot=self,
                        post=post,
                        chat_ids=chat_ids if isinstance(chat_ids, list) else [chat_ids],
                        **settings,
                    )
                    sender.send_post()

                self.config["domains"][domain]["last_id"] = group.last_id
                self.config["domains"][domain]["last_story_id"] = group.last_story_id
                self.config["domains"][domain]["pinned_id"] = group.pinned_id

                self.save_config()

                for data in self.cache_dir.iterdir():
                    data.unlink()
        logger.info("[VK] Работа завершена")

    def reload_config(self):
        with self.config_path.open() as stream:
            self.config: dict = yaml.safe_load(stream)

    def save_config(self):
        with self.config_path.open("w") as stream:
            yaml.dump(self.config, stream, indent=4)
