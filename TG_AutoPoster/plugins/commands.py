import os
import sys

import pyrogram.filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import AutoPoster
from ..utils import split
from ..utils.tg import messages, tools


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["start", "help"])
    & pyrogram.filters.private
    & tools.is_admin
)
def send_welcome(_, message: Message):
    button = [
        [
            InlineKeyboardButton(
                "Поиск среди источников", switch_inline_query_current_chat=""
            )
        ]
    ]
    message.reply(
        messages.HELP,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(button),
    )


@AutoPoster.on_message(
    pyrogram.filters.command(commands="get_full_logs")
    & pyrogram.filters.private
    & tools.is_admin
)
def send_full_logs(bot: AutoPoster, message: Message):
    logs = sorted(list(bot.logs_path.iterdir()))
    if logs:
        a = message.reply("Отправка логов...")
        try:
            a.reply_document(logs[-1])
        except ValueError:
            a.edit("Последний лог файл пустой")
    else:
        message.reply("Логи не найдены.")


@AutoPoster.on_message(
    pyrogram.filters.command(commands="get_last_logs")
    & pyrogram.filters.private
    & tools.is_admin
)
def send_last_logs(bot: AutoPoster, message: Message):
    logs = sorted(list(bot.logs_path.iterdir()))[-1]
    try:
        lines = int(message.command[1])
    except (ValueError, IndexError):
        lines = 15
    if logs:
        with logs.open() as f:
            last_logs = "".join(f.readlines()[-lines:])
            last_logs = (
                "Последние {} строк логов:\n\n".format(str(lines)) + last_logs
            )
        for msg in split(last_logs):
            message.reply(msg, parse_mode=ParseMode.DISABLED)
    else:
        message.reply("Логи не найдены.")


@AutoPoster.on_message(
    pyrogram.filters.command(
        commands=["remove_source", "remove", "delete", "delete_source"]
    )
    & pyrogram.filters.private
    & tools.is_admin
)
def remove_source(bot: AutoPoster, message: Message):
    if len(message.command) > 1:
        bot.reload_config()
        section = {
            **dict(last_id=0, last_story_id=0, pinned_id=0),
            **bot.config["domains"].pop(message.command[1]),
        }
        bot.save_config()
        info = messages.SECTION_DELETED.format(message.command[1], **section)
        message.reply(info)
    else:
        message.reply(messages.REMOVE)


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["add"])
    & pyrogram.filters.private
    & tools.is_admin
)
def add_source(bot: AutoPoster, message: Message):
    if len(message.command) >= 3:
        bot.reload_config()
        if not bot.config.get("domains"):
            bot.config["domains"] = {}
        bot.config["domains"][message.command[1]] = dict(
            zip(
                ("channel", "last_id", "pinned_id", "last_story_id"),
                (int(i) if i.isnumeric() else i for i in message.command[2:]),
            )
        )
        info = "Источник `{}` был добавлен.".format(message.command[1])
        bot.save_config()
        message.reply(info)
    else:
        message.reply(messages.ADD, parse_mode=ParseMode.MARKDOWN)


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["settings"])
    & pyrogram.filters.private
    & tools.is_admin
)
def settings(bot: AutoPoster, message: Message):
    bot.reload_config()
    info, reply_markup = tools.generate_setting_info(bot, "global")
    message.reply(info, reply_markup=reply_markup)


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["get_config"])
    & pyrogram.filters.private
    & tools.is_admin
)
def get_config(bot: AutoPoster, message: Message):
    message.reply(
        "Конфигурация бота:\n```{}```".format(
            bot.config_path.read_text(encoding="utf-8")
        )
    )
    message.reply_document(
        document=bot.config_path, caption="Файл конфигурации бота."
    )


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["register"])
    & pyrogram.filters.private
)
def register(bot: AutoPoster, message: Message):
    if len(message.command) >= 2:
        if message.command[1] == bot.bot_token:
            bot.reload_config()
            bot.admins_id.append(message.from_user.id)
            if bot.config.get("settings"):
                bot.config["settings"]["admins_id"] = bot.admins_id
            else:
                bot.config["settings"] = {
                    "admins_id": bot.admins_id,
                }
            bot.save_config()
            message.reply("Вы были добавлены в список администраторов")


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["update_stoplist"])
    & pyrogram.filters.private
    & tools.is_admin
)
def update_stoplist(bot: AutoPoster, message: Message):
    domain = message.command[1] if len(message.command) >= 2 else "global"
    if domain != "global":
        if domain not in bot.config["domains"].keys():
            message.reply(f"Источник `{domain}` не найден.")
            return
    bot.conversations.update(
        {message.from_user.id: ("stop_list", domain)}
    )
    message.reply(messages.STOPLIST_UPDATE)


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["delete_stoplist", "delete_blacklist"])
    & pyrogram.filters.private
    & tools.is_admin
)
def delete_stoplist(bot: AutoPoster, message: Message):
    bot.reload_config()
    if message.command[0].split("_")[1] == "stoplist":
        filetype = "stop_list"
    else:
        filetype = "blacklist"

    domain = message.command[1] if len(message.command) >= 2 else "global"
    if domain == "global":
        if filetype in bot.config.get("settings", {}).keys():
            os.remove(bot.config["settings"][filetype])
            bot.config["settings"].pop(filetype)
    else:
        if domain in bot.config["domains"].keys():
            if filetype in bot.config["domains"][domain].keys():
                os.remove(bot.config["domains"][domain][filetype])
                bot.config["domains"][domain].pop(filetype)
        else:
            message.reply(f"Источник `{domain}` не найден.")
            return

    message.reply(
        getattr(messages, f"{filetype.replace('_', '').upper()}_DELETED")
    )
    bot.save_config()


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["update_blacklist"])
    & pyrogram.filters.private
    & tools.is_admin
)
def update_blacklist(bot: AutoPoster, message: Message):
    domain = message.command[1] if len(message.command) >= 2 else "global"
    if domain != "global":
        if domain not in bot.config["domains"].keys():
            message.reply(f"Источник `{domain}` не найден.")
            return
    bot.conversations.update(
        {message.from_user.id: ("blacklist", domain)}
    )
    message.reply(messages.BLACKLIST_UPDATE)


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["restart"])
    & pyrogram.filters.private
    & tools.is_admin
)
def restart(bot: AutoPoster, message: Message):
    if sys.platform.startswith("win32"):
        message.reply("Команда не доступна в Windows.")
    else:
        message.reply("Перезапуск бота...")
        os.chdir(bot.config_path.parent)
        os.execv(sys.executable, [sys.executable] + sys.argv)


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["exit"])
    & pyrogram.filters.private
    & tools.is_admin
)
def exit_(_, message: Message):
    if sys.platform.startswith("win32"):
        message.reply("Команда не доступна в Windows.")
    else:
        message.reply("Завершение работы...")
        sys.exit(0)

@AutoPoster.on_message(
    pyrogram.filters.command(commands=["cancel"]) & pyrogram.filters.private
)
def cancel(bot: AutoPoster, message: Message):
    if message.from_user.id in bot.conversations.keys():
        message.reply("Операция отменена.")
        bot.conversations.pop(message.from_user.id)


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["about"]) & pyrogram.filters.private
)
def about(_, message: Message):
    message.reply(messages.ABOUT, disable_web_page_preview=True)


@AutoPoster.on_message(pyrogram.filters.command(commands=["get_id"]))
def get_id(_, message: Message):
    message.reply("Chat id is `{}`".format(message.chat.id))

