from typing import List, Tuple, Union

from loguru import logger
from pyrogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
                            InlineQuery, Message)

from ..tools import build_menu
from . import messages


def admin_check(bot, message: Union[Message, InlineQuery, CallbackQuery]) -> bool:
    if isinstance(message, Message):
        logger.info(
            messages.LOG_MESSAGE,
            message=message,
        )
        if not bot.admins_id:
            message.reply(messages.ACCESS_DENIED)
    elif isinstance(message, InlineQuery):
        logger.info(
            messages.LOG_INLINE_QUERY,
            message=message,
        )
    elif isinstance(message, CallbackQuery):
        logger.info(
            messages.LOG_CALLBACK_QUERY,
            message=message,
        )
    return message.from_user.id in bot.admins_id


def generate_setting_info(bot, domain: str) -> Tuple[str, InlineKeyboardMarkup]:
    settings = {
        **bot.config.get("settings", {}),
        **bot.config["domains"].get(domain, {}),
    }
    if domain != "global":
        text = messages.INLINE_INPUT_MESSAGE_CONTENT.format(
            domain.replace("https://vk.com/", "").replace("https://m.vk.com/", ""),
            bot.config["domains"][domain]["channel"],
            bot.config["domains"][domain].get("last_id", 0),
            bot.config["domains"][domain].get("last_story_id", 0),
            bot.config["domains"][domain].get("pinned_id", 0),
        ) + "Отправляемые вложения: `{}`".format(settings.get("what_to_send", "всё"))
        footer_button = [
            InlineKeyboardButton("Удалить источник", callback_data="delete " + domain)
        ]
    else:
        text = messages.GLOBAL_SETTINGS.format(settings.get("what_to_send", "всё"))
        footer_button = None
    reposts = settings.get("send_reposts", 0)
    if reposts == "post_only":
        reposts = "Только пост"
        text += messages.PARTIAL_REPOSTS
    elif reposts:
        reposts = "✔️"
    elif not reposts:
        reposts = "❌"
    button_list = [
        InlineKeyboardButton(
            "Подписи: {}".format("✔️" if settings.get("sign_posts", True) else "❌"),
            callback_data="switch {} sign_posts".format(domain),
        ),
        InlineKeyboardButton(
            "Репосты: {}".format(reposts),
            callback_data="show {} send_reposts".format(domain),
        ),
        InlineKeyboardButton(
            "Уведомления: {}".format(
                "❌" if settings.get("disable_notification", False) else "✔️"
            ),
            callback_data="switch {} disable_notification".format(domain),
        ),
        InlineKeyboardButton(
            "Истории: {}".format("✔️" if settings.get("send_stories", False) else "❌"),
            callback_data="switch {} send_stories".format(domain),
        ),
        InlineKeyboardButton(
            "Превью ссылок: {}".format(
                "❌" if settings.get("disable_web_page_preview", True) else "✔️"
            ),
            callback_data="switch {} disable_web_page_preview".format(domain),
        ),
        InlineKeyboardButton(
            "Отправляемые вложения",
            callback_data="show {} wts".format(domain),
        ),
    ]

    return text, InlineKeyboardMarkup(
        build_menu(button_list, footer_buttons=footer_button, n_cols=2)
    )


def generate_what_to_send_info(bot, domain: str) -> Tuple[str, InlineKeyboardMarkup]:
    settings = {
        **bot.config.get("settings", {}),
        **bot.config["domains"].get(domain, {}),
    }

    info = "**Настройка отправки вложений:**\n\n"

    button_list = [
        InlineKeyboardButton(
            messages.ATTACHMENTS_TYPES[key].format(
                "✔"
                if key in settings.get("what_to_send", ["all"])
                or "all" in settings.get("what_to_send", ["all"])
                else "❌"
            ),
            callback_data="wts {} {}".format(domain, key),
        )
        for key in messages.ATTACHMENTS_TYPES.keys()
    ]

    footer_buttons = [
        InlineKeyboardButton(
            "Отправлять всё",
            callback_data="wts {} all".format(domain),
        )
    ]

    return info, InlineKeyboardMarkup(
        build_menu(button_list, footer_buttons=footer_buttons, n_cols=2)
    )


def change_what_to_send_setting(what_to_send: List, value: str) -> List:
    attach_types = messages.ATTACHMENTS_TYPES.keys()
    if "all" in what_to_send:
        what_to_send = [i for i in attach_types if i != value]
    else:
        if value in what_to_send:
            what_to_send.remove(value)
        else:
            what_to_send.append(value)
        if set(what_to_send) == set(attach_types) or value == "all":
            what_to_send = ["all"]

    return what_to_send