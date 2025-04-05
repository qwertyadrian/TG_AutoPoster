TG_AutoPoster 
=============
Бот, пересылающий записи из групп ВК в канал/чат/ЛС в Telegram.

[![License MIT](https://img.shields.io/github/license/qwertyadrian/TG_AutoPoster.svg)](/LICENCE.md) 
![Python Version](https://img.shields.io/pypi/pyversions/tg_autoposter) 
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![issues](https://img.shields.io/github/issues/qwertyadrian/TG_AutoPoster.svg)](https://github.com/qwertyadrian/TG_AutoPoster/issues) 
[![stars](https://img.shields.io/github/stars/qwertyadrian/TG_AutoPoster.svg)](https://github.com/qwertyadrian/TG_AutoPoster/stargazers)
[![PyPI](https://img.shields.io/pypi/v/TG-AutoPoster)](https://pypi.org/project/TG-AutoPoster/)
[![docker](https://img.shields.io/badge/docker%20image-tg__autoposter-FF9900)](https://hub.docker.com/r/qwertyadrian/tg_autoposter)
***
### Установка (обновление)
```shell script
pip3 install -U TG-AutoPoster
```
***
### Настройка
1. Создайте файл `config.yaml`, скопируйте в него содержимое файла [config.yaml.example](/config.yaml.example) и выполните настройку ключа `vk`

|                 Параметр                 |                                                                                                                                                                                                        Описание                                                                                                                                                                                                         |
|:----------------------------------------:|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
|                  login                   |                                                                                                                                                                                                        Логин ВК                                                                                                                                                                                                         |
|                   pass                   |                                                                                                                                                                                                        Пароль ВК                                                                                                                                                                                                        |
|          token (необязательно)           | **Рекомендуется к использованию.** Cервисный ключ доступа или ключ доступа пользователя ([подробнее](https://vk.com/dev/access_token)). Если он задан, то логин и пароль игнорируются. При его использовании не будут доступны аудиозаписи (при использовании сервисного ключа доступа также не будут доступны истории). Получить ключ доступа пользователя можно с помощью [этого](https://vkhost.github.io/) сервиса. | 

2. Получите ваши `api_id` и `api_hash` на https://my.telegram.org/apps и настройте ключ `telegram` (подробнее об Telegram API Keys [здесь](https://docs.pyrogram.org/intro/setup#api-keys))

| Параметр  |                                Описание                                |
|:---------:|:----------------------------------------------------------------------:|
|  api_id   |                               App api_id                               |
| api_hash  |                              App api_hash                              |
| bot_token | Токен Telegram бота, полученный у [@BotFather](https://t.me/BotFather) |

3. Если необходимо, настройте использование SOCKS5 прокси, добавив ключ `proxy` со следующим содержимым:

|         Параметр         | Возможные значения |                Описание                |
|:------------------------:|:------------------:|:--------------------------------------:|
|         enabled          |    true, false     |         Использовать ли прокси         |
|         hostname         |                    |  IP адрес (или домен) прокси сервера   |
|           port           |                    |          Порт прокси сервера           |
| username (необязательно) |                    |            Имя пользователя            |
| password (необязательно) |                    |                 Пароль                 |

### Запуск                                                                                                                                                                                                                                                                                                                                                            
1. Для запуска используйте консольную команду `python3 -m TG_AutoPoster`     
2. Активируйте бота в чате командой `/start`

Автопостинг **рекомендуется** настраивать через чат с ботом. Подробнее можно узнать, отправив боту команду `/help`

Для доступных параметров командой строки используйте `python3 -m TG_AutoPoster --help`

По умолчанию бот проверяет группы на наличие новых постов раз в час. Если необходимо изменить период проверки постов
запустите бота с параметром командной строки `--sleep N`, где N — значение в секундах. Не рекомендуется устанавливать
малое значение, так как это может привести к заморозке страницы ВК ([подробнее](https://github.com/qwertyadrian/TG_AutoPoster/issues/22)).

***
#### Описание настроек группы

|           Параметр            |                                                                                                                                                                                                                                            Описание                                                                                                                                                                                                                                            |
|:-----------------------------:|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
|            channel            |                                                                                                                                                                                                     Один или несколько ID каналов/чатов в Telegram, в которые отправлять посты из групп ВК                                                                                                                                                                                                     |
|    last_id (необязательно)    |                                                                                                                                                                                          ID последнего отправленного поста. Если параметр отсутствует, он будет добавлен автоматически со значением 0                                                                                                                                                                                          |
|   pinned_id (необязательно)   |                                                                                                                                                                                                                                    ID закреплённого поста.                                                                                                                                                                                                                                     |
| last_story_id (необязательно) |                                                                                                                                                                                                                               ID последней отправленной истории.                                                                                                                                                                                                                               |
| use_long_poll (необязательно) | Использовать [Long Poll API](https://vk.com/dev/bots_longpoll) для получения постов из **своей** группы (или в которой вы являетесь администратором) в режиме реального времени. Чтобы использовать Long Poll API, откройте раздел «Управление сообществом», на вкладке «Работа с API»→«Long Poll API» выберите «Включено», «Версия API»: 5.131. Также необходимо включить тип события «Записи на стене»: «Добавление» на вкладке «Типы событий».<br/>Значение параметра по умолчанию: `false` |


#### Описание настроек автопостинга (ключ `settings`)

|         Параметр         |                                    Возможные значения                                     |                                                                                 Описание                                                                                 |
|:------------------------:|:-----------------------------------------------------------------------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
|        sign_posts        |                                        true, false                                        |                                    Указывать ли автора поста (если это возможно) и ссылку на оригинальный пост. По умолчанию: `true`                                     |
|       send_reposts       |                                  false, post_only, true                                   |                        Отправлять ли репосты? Подробнее в [config.yaml.example](/config.yaml.example). По умолчанию отправка репостов отключена.                         |
|       send_stories       |                                        false, true                                        |                                                               Отправлять ли истории? По умолчанию: `false`                                                               |
|       what_to_send       |                     all, text, link, photo, doc, video, music, polls                      |                     Какие типы вложений отправлять. Подробнее в [config.yaml.example](/config.yaml.example). По умолчанию отправляются все вложения.                     |
|        stop_list         |                                                                                           | Абсолютный путь к файлу, содержащий стоп-слова (по одному слову на каждой строке). Если вы не хотите использовать стоп-слова удалите этот параметр из файла конфигурации |
|     invert_stop_list     |                                        true, false                                        |        Инвертировать список стоп-слов (по умолчанию отключено). Будут отправляться посты, в которых содержатся указанные в списке слова или регулярные выражения         |
|        blacklist         |                                                                                           |                   Абсолютный путь к файлу, содержащий слова, которые будут удалены из текста отправляемого поста. Поддерживаются регулярные выражения.                   |
|   disable_notification   |                                        true, false                                        |                                      Отправляет сообщения молча. Пользователи получат уведомление без звука. По умолчанию: `false`                                       |
| disable_web_page_preview |                                        true, false                                        |                                                     Отключить предпросмотр ссылок в сообщениях. По умолчанию: `true`                                                     |
|       posts_count        |                                                                                           |                                                   Количество отправляемых ботом новых постов за раз. По умолчанию 11.                                                    |
|          header          | Текст с форматированием [Markdown](https://core.telegram.org/bots/api#formatting-options) |                                                             Текст, который будет добавлен в начало сообщения                                                             |
|          footer          |                             Текст с форматированием Markdown                              |                                                             Текст, который будет добавлен в конец сообщения                                                              |

Все параметры ключа `settings` могут быть заданы индивидуально для каждой группы
***
Дополнительно:
[Использование Docker контейнера](/Docker.md)

Отчеты об ошибках и предложения отправлять в:
1. [GitHub Issues](https://github.com/qwertyadrian/TG_AutoPoster/issues/new/choose)
2. Telegram: [@QwertyAdrian](https://t.me/QwertyAdrian)

Для пожертвований на развитие проекта:
1. Bitcoin: `1H1UVnXgvcLo3RWmxuYmi7b16ADo6XBWw5`
2. TON: `EQD42Z5d8d1gT1uSpKTAaLYHlQ95vdMXrlNlYMpSFpQawwuY`
