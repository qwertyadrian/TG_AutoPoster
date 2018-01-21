Это исходный код бота, который пересылает записи из групп ВК в канал/чат/ЛС в Telegram. Чтобы им воспользоваться, нужно скачать на компьютер файлы AutoPoster_bot.py, config.py и last_known_id.txt. Затем в файле cofig.py вы должны задать значения переменных указанных в файле.
Переменная TOKEN - это токен бота в телеграмме, который создан с помощью BotFather. 
Переменная GROUP - краткое название группы в ВК(то, что указывается в ссылке, например, https://vk.com/test_group123 значит GROUP = 'test_group123')
Переменная TOKEN_VK - это ваш access_token ВК, чтобы его получить можно перейти по этой [ссылке](https://oauth.vk.com/authorize?client_id=2890984&scope=notify,photos,friends,audio,video,notes,pages,docs,status,questions,offers,wall,groups,messages,notifications,stats,ads,offline&redirect_uri=http://api.vk.com/blank.html&display=page&response_type=token), после того, как вы перешли по ссылке и авторизировались, нужно из адресной строки браузера скопировать ту часть ссылки где указано access_token=(например, http://api.vk.com/blank.html#access_token=12345abc&expires_in=0&user_id=12345678, значит переменая TOKEN_VK = '12345abc'). 
Переменная CHAT_ID - это ссылка на канал/чат Telegram(например, CHAT_ID = '@channel') или это ваш ID Telegram (его можно узнать у @my_id_bot). 
Затем просто сохраните файл config.py и запустите файл AutoPoster_bot.py Но чтобы бот отправлял сообщения в канал он должен быть администратором канала, а чтобы он отправлял вам сообщения в ЛС нужно его активировать.