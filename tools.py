# Символы, на которых можно разбить сообщение
message_breakers = ["\n", ", "]


def update_parameter(config, section, name, num, config_path="../config.ini") -> int:
    config.set(section, name, str(num))
    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)
    return num


def split(text: str, max_message_length=4091) -> list:
    """ Разделение текста на части

    :param text: Рабиваемый текст
    :param max_message_length: Максимальная длина рабитой части текста
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
