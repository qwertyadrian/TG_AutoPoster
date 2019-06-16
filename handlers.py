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