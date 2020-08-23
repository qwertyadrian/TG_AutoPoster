#!/usr/bin/env bash
# Скрипт запускающий бота TG_AutoPoster с поддержкой виртуального окружения virtualenv
# Вы можете запускать данный скрипт по расписанию с помощью crontab
# Для отключения вывода информации в консоль добавьте > /dev/null 2>&1

PYTHON_EXECUTABLE="python3" # Имя файла интерпретатора Python


if [ -n "${ENV_PATH}" ] # Проверка существования переменной
then # Если переменная существует
    : # то ничего не делаем
else
    ENV_PATH="venv" # иначе используем значение по умолчанию
fi


if [[ $1 = 'edit' ]]
then
    if [[ -x ${EDITOR} ]]
    then
        ${EDITOR} config.ini
    else
        echo 'Variable environment EDITOR is not set. Edit file config.ini manually.'
    fi
else
    if [[ -d ${ENV_PATH} ]]
    then
        echo "Activating virtual environment."
        . ${ENV_PATH}/bin/activate
        echo "Запуск бота."
        if ! ${PYTHON_EXECUTABLE} -m TG_AutoPoster "$@"
        then
            echo -e "\e[41mПрограмма завершилась неудачно. Смотрите логи.\e[0m"
        fi
        echo "Бот завершил свою работу. Деактивация виртуального окружения."
        echo "Выход."
        deactivate
    else
        echo "Папка с виртуальным окружением не найдена или задана не правильно."
        echo "Попытка запуска бота без виртуального окружения."
        if ! ${PYTHON_EXECUTABLE} -m TG_AutoPoster "$@"
        then
            echo -e "\e[41mПрограмма завершилась неудачно. Смотрите логи.\e[0m"
        fi
        echo "Бот завершил свою работу. Выход."
    fi
fi
