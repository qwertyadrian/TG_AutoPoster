# Символы, на которых можно разбить сообщение
message_breakers = [':', ' ', '\n']
max_message_length = 4091


def update_parameter(config, section, name, num) -> int:
    config.set(section, name, str(num))
    with open('../config.ini', 'w', encoding='utf-8') as f:
        config.write(f)
    return num


def split(text):
    if len(text) >= max_message_length:
        last_index = max(
            map(lambda separator: text.rfind(separator, 0, max_message_length), message_breakers))
        good_part = text[:last_index]
        bad_part = text[last_index + 1:]
        return [good_part] + split(bad_part)
    else:
        return [text]

