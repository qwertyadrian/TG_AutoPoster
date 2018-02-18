TOKEN = ''  # Токен Telegram бота
GROUP_1 = ''  # Ссыка на группу ВК (Например, https://vk.com/test123, значит GROUP_1 = 'test123')
CHAT_ID_1 = ''  # Ссылка на канал/супергруппу или ID пользователя Telegram
FILENAME_VK_1 = 'last_known_id_1.txt'  # Файл для сохранения ID последнего отправленного поста. Для каждой группы используется отдельный файл.
BASE_VIDEO_URL = 'https://vk.com/video'  # Базовая ссылка для обработки видео
URLS = {GROUP_1: (FILENAME_VK_1, CHAT_ID_1)}  # Словарь со значинями выше. Может быть расширен для работы несколькими группами ВК.
LOGIN = ''  # Логин ВК
PASSWORD = ''  # Пароль ВК


def auth_handler():
    """
    При двухфакторной аутентификации вызывается эта функция.
    :return: key, remember_device
    """
    num = input('Введите код авторизации')
    remember_device = True
    return num, remember_device
