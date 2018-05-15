TOKEN = ''  # Токен Telegram бота
GROUP = ''  # Ссыка на группу ВК (Например, https://vk.com/test123, значит GROUP_1 = 'test123')
CHAT_ID = ''  # Ссылка на канал/супергруппу или ID пользователя Telegram
FILENAME_VK = '../last_known_id_1.txt'  # Файл для сохранения ID последнего отправленного поста. Для каждой группы используется отдельный файл.
BASE_VIDEO_URL = 'https://vk.com/video'  # Базовая ссылка для обработки видео
URLS = {GROUP: (FILENAME_VK, CHAT_ID)}  # Словарь со значинями выше. Может быть расширен для работы несколькими группами ВК.
LOGIN = None  # Логин ВК
PASSWORD = None  # Пароль ВК
ACCESS_TOKEN = None  # Ключ доступа к VK API
INVERT = True  # Если True, то сначала будет отправляться приложенные к посту фото, а затем текст поста. Если False, то будет наоборот.
SIGN = True # Оставлять ли ссылку на оригинал поста и на его автора.
SINGLE_RUN = 1  # Если указана 1, то программа будет выполнена лишь 1 раз. Если указан 0, то программа будет работать пока она не будет остановлена вручную.
proxy_url = "https://89.236.17.106:3128"  # HTTPS Прокси


def auth_handler():
    """
    При двухфакторной аутентификации вызывается эта функция.
    :return: key, remember_device
    """
    num = input('Введите код авторизации')
    remember_device = True
    return num, remember_device


def captcha_handler(captcha):
    key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()
    return captcha.try_again(key)
