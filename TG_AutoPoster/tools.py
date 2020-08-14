import subprocess
import time

# Символы, на которых можно разбить сообщение
message_breakers = ["\n", ", "]


def update_parameter(config, section, name, num, config_path="../config.ini") -> int:
    config.set(section, name, str(num))
    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)
    return num


def split(text: str, max_message_length: int = 4091) -> list:
    """ Разделение текста на части

    :param text: Разбиваемый текст
    :param max_message_length: Максимальная длина разбитой части текста
    """
    if len(text) >= max_message_length:
        last_index = max(map(lambda separator: text.rfind(separator, 0, max_message_length), message_breakers))
        good_part = text[:last_index]
        bad_part = text[last_index + 1:]
        return [good_part] + split(bad_part, max_message_length)
    else:
        return [text]


def list_splitter(lst: list, n: int) -> list:
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def start_process(command: list) -> int:
    process = subprocess.Popen(command)
    while process.poll() is None:
        time.sleep(1)
    return process.returncode
