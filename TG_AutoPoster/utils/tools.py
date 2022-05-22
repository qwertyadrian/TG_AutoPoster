from pyrogram.types import InlineKeyboardButton

# Символы, на которых можно разбить сообщение
message_breakers = [":", " ", "\n"]


def split(text: str, max_message_length: int = 4091) -> list:
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
    buttons: list[InlineKeyboardButton],
    n_cols: int = 1,
    header_buttons: list[InlineKeyboardButton] = None,
    footer_buttons: list[InlineKeyboardButton] = None,
) -> list[list[InlineKeyboardButton]]:
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu
