import pyrogram.filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import AutoPoster
from ..utils import split
from ..utils.tg import messages, tools


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["start", "help"]) & pyrogram.filters.private
)
def send_welcome(bot: AutoPoster, message: Message):
    if tools.admin_check(bot, message):
        button = [
            [
                InlineKeyboardButton(
                    "Поиск среди источников", switch_inline_query_current_chat=""
                )
            ]
        ]
        message.reply(
            messages.HELP,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(button),
        )


@AutoPoster.on_message(
    pyrogram.filters.command(commands="get_full_logs") & pyrogram.filters.private
)
def send_full_logs(bot: AutoPoster, message: Message):
    if tools.admin_check(bot, message):
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
    pyrogram.filters.command(commands="get_last_logs") & pyrogram.filters.private
)
def send_last_logs(bot: AutoPoster, message: Message):
    if tools.admin_check(bot, message):
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
)
def remove_source(bot: AutoPoster, message: Message):
    if tools.admin_check(bot, message):
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
    pyrogram.filters.command(commands=["add"]) & pyrogram.filters.private
)
def add_source(bot: AutoPoster, message: Message):
    if tools.admin_check(bot, message):
        if len(message.command) >= 3:
            bot.reload_config()
            bot.config["domains"][message.command[1]] = dict(
                zip(
                    ["channel", "last_id", "pinned_id", "last_story_id"],
                    [int(i) if i.isnumeric() else i for i in message.command[2:]],
                )
            )
            info = "Источник {} был добавлен.".format(message.command[1])
            bot.save_config()
            message.reply(info)
        else:
            message.reply(messages.ADD, parse_mode=ParseMode.MARKDOWN)


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["settings"]) & pyrogram.filters.private
)
def settings(bot: AutoPoster, message: Message):
    if tools.admin_check(bot, message):
        bot.reload_config()
        info, reply_markup = tools.generate_setting_info(bot, "global")
        message.reply(info, reply_markup=reply_markup)


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["get_config"]) & pyrogram.filters.private
)
def get_config(bot: AutoPoster, message: Message):
    if tools.admin_check(bot, message):
        message.reply(
            "Конфигурация бота:\n```{}```".format(bot.config_path.read_text())
        )
        message.reply_document(
            document=bot.config_path, caption="Файл конфигурации бота."
        )


@AutoPoster.on_message(
    pyrogram.filters.command(commands=["register"]) & pyrogram.filters.private
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
    pyrogram.filters.command(commands=["about"]) & pyrogram.filters.private
)
def about(_, message: Message):
    message.reply(messages.ABOUT, disable_web_page_preview=True)


@AutoPoster.on_message(pyrogram.filters.command(commands=["get_id"]))
def get_id(_, message: Message):
    message.reply("Chat id is `{}`".format(message.chat.id))


@AutoPoster.on_message(pyrogram.filters.forwarded)
def get_forward_id(_, message: Message):
    if message.forward_from:
        id_ = message.forward_from.id
    else:
        id_ = message.forward_from_chat.id
    message.reply("Channel (user) ID is `{}`".format(id_))
