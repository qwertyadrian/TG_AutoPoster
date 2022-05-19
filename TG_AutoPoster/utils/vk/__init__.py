import os
from itertools import chain
from pathlib import Path

import yaml
from loguru import logger
from vk_api import VkApi

from ... import TG_AutoPoster
from .group import Group
from .handlers import auth_handler, captcha_handler
from .sender import Sender


def get_new_posts(
    bot: TG_AutoPoster.AutoPoster,
    config_path: Path,
    cache_dir: Path,
):
    config_path = config_path.absolute()
    cache_dir = cache_dir.absolute()

    try:
        os.chdir(cache_dir)
    except FileNotFoundError:
        cache_dir.mkdir()
        os.chdir(cache_dir)

    with open(config_path, "r") as stream:
        config: dict = yaml.safe_load(stream)

    if config["vk"].get("token"):
        vk_session = VkApi(token=config["vk"]["token"], api_version="5.131")
    else:
        logger.warning(
            "Использование логина и пароля не рекомендуется. "
            "Используйте ключ доступа пользователя."
        )
        vk_session = VkApi(
            login=config["vk"]["login"],
            password=config["vk"]["password"],
            auth_handler=auth_handler,
            captcha_handler=captcha_handler,
            api_version="5.131",
        )
    for domain in config["domains"].keys():
        group = Group(
            domain=domain,
            session=vk_session,
            **{**config.get("settings", {}), **config["domains"][domain]},
        )
        chat_ids = config["domains"][domain]["channel"]
        for post in chain(group.get_posts(), group.get_stories()):
            sender = Sender(
                bot=bot,
                post=post,
                chat_ids=chat_ids if isinstance(chat_ids, list) else [chat_ids],
            )
            sender.send_post()

            config["domains"][domain]["last_id"] = group.last_id
            config["domains"][domain]["last_story_id"] = group.last_story_id
            config["domains"][domain]["pinned_id"] = group.pinned_id

            with open(config_path, "w") as stream:
                yaml.dump(config, stream, indent=4)

            for data in cache_dir.iterdir():
                data.unlink()
