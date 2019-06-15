# TG_AutoPoster 
Бот, пересылающий записи из групп ВК в канал/чат/ЛС в Telegram.

![License MIT](https://img.shields.io/github/license/qwertyadrian/TG_AutoPoster.svg) ![Python Version](https://img.shields.io/badge/python-3.5%2B-orange.svg)
![issues](https://img.shields.io/github/issues/qwertyadrian/TG_AutoPoster.svg) ![stars](https://img.shields.io/github/stars/qwertyadrian/TG_AutoPoster.svg)
***
## Установка
1. Клонируйте репозиторий
```bash
git clone https://github.com/qwertyadrian/TG_AutoPoster
```
2. Установите требуемые зависимости (желательно использовать виртуальное окружние)
```bash
pip install -r requirements.txt
```
3. Скопируйте содердимое файла [config.ini.example](/config.ini.example) в файл config.ini (создайте его, разумеется) и выполните настройку поля **global**

| Параметр      | Описание  |
| :-------------: | :-----:|
| login | Логин ВК |
| pass | Пароль ВК |
| bot_token | Токен Telegram бота |
| sign_posts | Указывать ли автора поста (если это возможно) и ссылку на оригинальный пост. Возмжные значения: yes, no |
| send_reposts | Отправлять ли репосты. Возможные значения: yes, no |
| proxy_url | HTTPS Прокси (использовать, если Telegram не доступен в вашей стране) |
| admin |  ID администратора бота (пока не используется, не заполнять) |
| main_group | Не используется (не заполнять) |
| what_to_send | Какие типы вложений отправлять. Подробнее в [config.ini.example](/config.ini.example) |
4. Замените название поля с **domain1** на домен группы ВК и выполните соответствующую настройку этого поля.

| Параметр | Описание |
| :------: | :------: |
| channel | Канал/чат в телеграме куда отправлять сообщения из групп ВК |
| last_id | ID последнего отправленного поста |

**Для работы с несколькими группами добавьте новые поля в соответствии с пунктом № 4**
## Запуск

5. Пропишите запуск файла по расписанию [TG_AutoPoster.py](/TG_AutoPoster.py) в crontab (в Linux) или планировщик заданий Windows (нежелательно запускать бота каждые 5-10 минут, так как за это возможна заморозка вашего профиля ВК)
6. Активириуйте бота командой /start
7. Готово!

Вопрсы и предложения:
1. Telegram: [@QwertyAdrian](https://tlg.name/QwertyAdrian)
2. Вконтакте: [Адриан Поляков](https://vk.com/qwertyadrian) (отвечаю там редко)