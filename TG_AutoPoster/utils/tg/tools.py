from typing import Tuple, Union

from loguru import logger
from pyrogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
                            InlineQuery, Message)

from . import messages
from ..tools import build_menu


def admin_check(
    bot, message: Union[Message, InlineQuery, CallbackQuery]
) -> bool:
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


def generate_setting_info(
    bot, domain: str
) -> Tuple[str, InlineKeyboardMarkup]:
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
    ]

    return text, InlineKeyboardMarkup(
        build_menu(button_list, footer_buttons=footer_button, n_cols=2)
    )
