# TG_AutoPoster 
Бот, пересылающий записи из групп ВК в канал/чат/ЛС в Telegram.

![License MIT](https://img.shields.io/github/license/qwertyadrian/TG_AutoPoster.svg) ![Python Version](https://img.shields.io/badge/python-3.5%2B-orange.svg)
![issues](https://img.shields.io/github/issues/qwertyadrian/TG_AutoPoster.svg) ![stars](https://img.shields.io/github/stars/qwertyadrian/TG_AutoPoster.svg)
![docker](https://img.shields.io/badge/docker%20image-tg__autoposter-FF9900)
***
## Установка
1. Клонируйте репозиторий
```bash
git clone https://github.com/qwertyadrian/TG_AutoPoster
```
2. Инициализуруйте подмодули (необходимо, если вам нужен TG_AutoConfigurator)
```bash
git submodule update --init --recursive
```
3. Установите требуемые зависимости (желательно использовать виртуальное окружние)
```bash
pip install -r requirements.txt
pip install -r TG_AutoConfigurator/requirements.txt
```
4. Скопируйте содердимое файла [config.ini.example](/config.ini.example) в файл config.ini (создайте его, разумеется) и выполните настройку поля **global**

| Параметр      | Описание  |
| :-------------: | :-----:|
| login | Логин ВК |
| pass | Пароль ВК |
| bot_token | Токен Telegram бота |
| sign_posts | Указывать ли автора поста (если это возможно) и ссылку на оригинальный пост. Возмжные значения: yes, no |
| send_reposts | Отправлять ли репосты. Возможные значения: yes, no |
| proxy_url | HTTPS Прокси (использовать, если Telegram не доступен в вашей стране) |
| what_to_send | Какие типы вложений отправлять. Подробнее в [config.ini.example](/config.ini.example) |
| stop_list (необязательно)| Путь к файлу, содержащий стоп-слова (в файле должно быть по одному слову на каждой строке). Если вы не хотите использовать стоп-слова удалите этот параметр из файла конфигурации |
5. Замените название поля с **domain1** на домен группы ВК и выполните соответствующую настройку этого поля.

| Параметр | Описание |
| :------: | :------: |
| channel | Канал/чат в телеграме куда отправлять сообщения из групп ВК |
| last_id | ID последнего отправленного поста |
| what_to_send | Какие типы вложений отправлять (переопределяет значение из global) |

**Для работы с несколькими группами добавьте новые поля в соответствии с пунктом № 4**
## Запуск

6. Пропишите запуск файла по расписанию [TG_AutoPoster.py](/TG_AutoPoster.py) в crontab (в Linux) или планировщик заданий Windows (нежелательно запускать бота каждые 5-10 минут, так как за это могут заморозить ваш профиль ВК)
7. Активириуйте бота командой /start
8. Готово!
***
Дополнительно:
Если вы хотите управлять автопостингом через Telegram чат , то предлагаю ознакомиться с [TG_AutoConfigurator](https://github.com/qwertyadrian/TG_AutoConfigurator).  
Сейчас он умеет: смотреть логи, удалять/добавлять/просматривать источники постов  
Запланировано для него следующее: настройка отправляемых вложений (в том числе отдельно для каждой группы), управление несколькими ботами  
***

## NEW Docker контейнер
Теперь бот доступен в виде Docker контейнера
### Порядок установки
1. Установите Docker
2. Получите образ контейнера с помощью команды:
```bash
docker pull qwertyadrian/tg_autoposter
```
3. Запустите docker контейнер командой (должно завершиться с ошибкой)
```bash
docker run -it --name <имя_контейнера> tg_autoposter
```
4. Скопируйте файл конфигурации config.ini в созданный контейнер командой:
```bash
docker cp <путь_до_файла_конфигурации> <имя_контейнера>:/TG_AutoPoster/config.ini
```
5. Повторно запустите контейнер командой (параметр `-i` необходим только для интерактивного режима, для запуска в фоне можно опустить):
```bash
docker start -i <имя_контейнера>
```

Вопросы и предложения:
1. Telegram: [@QwertyAdrian](https://tlg.name/QwertyAdrian)
2. Вконтакте: [Адриан Поляков](https://vk.com/qwertyadrian) (отвечаю там редко)

Для пожертвований на развитие проекта:
1. Qiwi: [QwertyAdrian](https://qiwi.com/n/QWERTYADRIAN)
2. Яндекс.Деньги: 410012914796910
