import configparser
from botlogs import log
from vk_api import VkApi

config = configparser.ConfigParser()
config.read_file(open('../config.ini', 'r', encoding='utf-8'))
login = config.get('global', 'login')
password = config.get('global', 'pass')

session = None
api_vk = None


def setting(login: str=None, password: str=None, access_token: str=None) -> None:
    global session, api_vk
    session = VkApi(login=login, password=password, token=access_token, auth_handler=auth_handler,
                    captcha_handler=captcha_handler, config_filename='../vk_config.v2.json')
    if login and password:
        session.auth()
    api_vk = session.get_api()


def auth_handler():
    """
    При двухфакторной аутентификации вызывается эта функция.
    :return: key, remember_device
    """
    num = input('Введите код авторизации: ')
    remember_device = True
    return num, remember_device


def captcha_handler(captcha):
    key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()
    return captcha.try_again(key)


def update_parameter(section, name, num) -> int:
    config.set(section, name, str(num))
    with open('../config.ini', 'w', encoding='utf-8') as f:
        config.write(f)
    return num


def remove_section(section: str) -> None:
    config.remove_section(section)
    with open('../config.ini', 'w', encoding='utf-8') as f:
        config.write(f)


log.info('Запуск')
log.info('Авторизация на сервере ВК')
setting(config.get('global', 'login'), config.get('global', 'pass'))
