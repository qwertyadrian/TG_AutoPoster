# TG_AutoPoster 
Бот, пересылающий записи из групп ВК в канал/чат/ЛС в Telegram.

![License MIT](https://img.shields.io/github/license/qwertyadrian/TG_AutoPoster.svg) ![PyPI - Python Version](https://img.shields.io/badge/python-3.4%2C%203.5%2C%203.6-orange.svg)
![issues](https://img.shields.io/github/issues/qwertyadrian/TG_AutoPoster.svg) ![stars](https://img.shields.io/github/stars/qwertyadrian/TG_AutoPoster.svg)
***
## Установка
1. Клонируйте репозиторий
```bash
git clone https://github.com/qwertyadrian/TG_AutoPoster
```
2. Установите требуемые зависимости
```bash
pip install -r requirements.txt
```
3. Создайте файл config.ini и скопируйте в него содержимое файла [config.ini.example](/config.ini.example)
4. Выполните настройку поля **global** в созданном вами файле

| Параметр      | Описание  |
| :-------------: | :-----:|
| login | Логин ВК |
| pass | Пароль ВК |
| bot_token | Токен Telegram бота |
| sign_posts | Подписывать ли отправляемые сообщения |
| send_reposts | Отправлять ли репосты |
| check_interval | Время (в минутах), спустя которое будет начато получение новых постов (если есть) |
| proxy_url | HTTPS (SOCKS ) Прокси (использовать, если Telegram не доступен в вашей стране) |
| admin |  ID администратора бота (задается автоматически, после отправки боту его токена) |
| main_group | Канал/чат по умолчанию, в который отправлять одобренные посты пользователей |
5. Замените название поля с **domain1** на домен группы ВК и выполните соответствующую настройку этого поля.

| Параметр | Описание |
| :------: | :------: |
| channel | Канал/чат в телеграме куда отправлять сообщения из групп ВК |
| last_id | ID последнего отправленного поста |

**Для работы с несколькими группами добавьте новые поля в соответствии с пунктом № 5**
## Запуск

6. Активириуйте бота командой /start
7. Запустите файл [main.py](/main.py)
8. Готово!

Вопрсы и предложения:
1. Telegram: [@QwertyAdrian](https://t.me/QwertyAdrian)
2. Вконтакте: [Адриан Поляков](https://vk.com/qwertyadrian) (отвечаю там редко)