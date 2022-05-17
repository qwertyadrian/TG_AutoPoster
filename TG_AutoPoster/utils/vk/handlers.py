from threading import Thread
from time import sleep
from typing import Tuple

user_input = ["", None]


def auth_handler() -> Tuple[str, bool]:
    """
    При двухфакторной аутентификации вызывается эта функция.
    :return: key, remember_device
    """
    num = user_input[0]
    input_thread = Thread(target=get_auth_code, args=(user_input,))
    input_thread.daemon = True
    input_thread.start()
    for _ in range(120):
        sleep(1)
        if user_input[0] is not None:
            num = user_input[0]
            user_input[0] = None
            break
    if not num:
        raise TimeoutError("Время ожидания ввода истекло.")
    remember_device = True
    return num, remember_device


def captcha_handler(captcha):
    key = user_input[1]
    input_thread = Thread(target=get_captcha_code, args=(user_input, captcha))
    input_thread.daemon = True
    input_thread.start()
    for _ in range(120):
        sleep(1)
        if user_input[1] is not None:
            key = user_input[1]
            user_input[1] = None
            break
    if not key:
        raise TimeoutError("Время ожидания ввода истекло.")
    return captcha.try_again(key)


def get_auth_code(user_input_ref):
    user_input_ref[0] = input("Введите код авторизации: ")


def get_captcha_code(user_input_ref, captcha):
    user_input_ref[1] = input(
        "Enter captcha code {0}: ".format(captcha.get_url())
    ).strip()
