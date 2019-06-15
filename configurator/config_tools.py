import configparser


def remove_section(bot_config_path, section: str) -> tuple:
    config = configparser.ConfigParser()
    config.read_file(open(bot_config_path, 'r', encoding='utf-8'))
    channel = config.get(section, 'channel')
    last_id = config.get(section, 'last_id')
    config.remove_section(section)
    with open(bot_config_path, 'w', encoding='utf-8') as f:
        config.write(f)
    return section, channel, last_id


def add_section(bot_config_path, domain, chat_id, last_id='0', *args):
    config = configparser.ConfigParser()
    config.read_file(open(bot_config_path, 'r', encoding='utf-8'))
    domain = domain.replace('https://vk.com/', '').replace('https://m.vk.com/', '')
    config.add_section(domain)
    config.set(domain, 'channel', chat_id)
    config.set(domain, 'last_id', last_id)
    with open('../config.ini', 'w', encoding='utf-8') as f:
        config.write(f)
    return domain, chat_id, last_id
