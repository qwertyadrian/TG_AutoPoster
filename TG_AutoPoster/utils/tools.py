from functools import wraps
from time import sleep
from typing import List

from loguru import logger
from pyrogram.errors import FloodWait, SlowmodeWait
from pyrogram.types import InlineKeyboardButton

# Символы, на которых можно разбить сообщение
message_breakers = [":", " ", "\n"]


def split(text: str, max_message_length: int = 4091) -> List:
    """Разделение текста на части

    :param text: Разбиваемый текст
    :param max_message_length: Максимальная длина разбитой части текста
    """
    if len(text) >= max_message_length:
        last_index = max(
            map(
                lambda separator: text.rfind(separator, 0, max_message_length),
                message_breakers,
            )
        )
        good_part = text[:last_index]
        bad_part = text[last_index + 1 :]
        return [good_part] + split(bad_part, max_message_length)
    else:
        return [text]


def build_menu(
    buttons: List[InlineKeyboardButton],
    n_cols: int = 1,
    header_buttons: List[InlineKeyboardButton] = None,
    footer_buttons: List[InlineKeyboardButton] = None,
) -> List[List[InlineKeyboardButton]]:
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def timeout_handler(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except (FloodWait, SlowmodeWait) as e:
                logger.warning(e.MESSAGE, value=e.value)
                sleep(e.value)
            except (ConnectionError, AttributeError) as e:
                logger.error(
                    "{}. Ожидание 10 секунд. Если сообщение повторяется более 5 раз - перезапустите бота.",
                    e,
                )
                sleep(10)

    return wrapped
