# TG_AutoPoster 
Бот, пересылающий записи из групп ВК в канал/чат/ЛС в Telegram.

![Linecce MIT](https://img.shields.io/github/license/qwertyadrian/TG_AutoPoster.svg) ![PyPI - Python Version](https://img.shields.io/badge/python-3.4%2C%203.5%2C%203.6-orange.svg)
![issues](https://img.shields.io/github/issues/qwertyadrian/TG_AutoPoster.svg) ![stars](https://img.shields.io/github/stars/qwertyadrian/TG_AutoPoster.svg)
***
## Установка
1. Клонируйте репозиторий
```bash
git clone https://github.com/qwertyadrian/TG_AutoPoster
```
1. Установите требуемые зависимости
```bash
pip install -r requirements.txt
```
1. Выполните настройку файла [config.py](..blob/master/config.py)
| Переменная      | Тип           | Описание  |
| :------------- |:-------------:| :-----:|
| TOKEN    | str | Токен Telegram бота |
| GROUP    | str      |   Домен группы ВК (Например, https://vk.com/test123, значит GROUP = 'test123') |
| CHAT_ID | str      |    Ссылка на канал/супергруппу или ID пользователя Telegram |
| FILENAME_VK | str | Файл для сохранения ID последнего отправленного поста. Перед названием файла должно быть ../ Для каждой группы используется отдельный файл. |
| URLS | dict | Словарь со значинями выше. Может быть расширен для работы несколькими группами ВК. |
| LOGIN | str | Логин ВК |
| PASSWORD| str | Пароль ВК |
| ACCESS_TOKEN | str | Ключ доступа к VK API (не рекомендуется для использования) |
| proxy_url | str | HTTPS Прокси (использовать, если Telegram не доступен в вашей стране) |
**Дополнительные переменные указаны в файле.**
1. Активириуйте бота командой /start
1. Готово!

Вопрсы и предложения: [@QwertyAdrian](https://t.me/QwertyAdrian)