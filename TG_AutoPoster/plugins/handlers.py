import re
from pathlib import Path

import pyrogram.filters
from pyrogram.types import Message

from .. import AutoPoster
from ..utils.tg import messages, tools


@AutoPoster.on_message(pyrogram.filters.private & tools.status_filter("set"))
def update_header_footer(bot: AutoPoster, message: Message):
    _, domain, key = bot.conversations[message.from_user.id]
    bot.reload_config()
    if domain == "global":
        if message.text.markdown == "DELETE" and key in bot.config["settings"]:
            bot.config["settings"].pop(key)
        else:
            bot.config["settings"][key] = str(message.text.markdown)
    else:
        if message.text.markdown == "DELETE" and key in bot.config["domains"][domain]:
            bot.config["domains"][domain].pop(key)
        else:
            bot.config["domains"][domain][key] = str(message.text.markdown)
    bot.save_config()
    message.reply(messages.CHANGE_SUCCESS.format(key.capitalize()))
    bot.conversations.pop(message.from_user.id)


@AutoPoster.on_message(
    pyrogram.filters.private & (
            tools.status_filter("stop_list")
            | tools.status_filter("blacklist")
    )
)
def stoplist_update(bot: AutoPoster, message: Message):
    filetype, domain = bot.conversations[message.from_user.id]

    bot.reload_config()
    if domain == "global":
        global_stoplist = Path(bot.config.get("settings", {}).get(
            filetype,
            bot.config_path.parent / f"{filetype}_global.txt"
        ))
        bot.config.get("settings", {})[filetype] = str(global_stoplist)
        with global_stoplist.open("a", encoding="utf-8") as f:
            f.write(message.text + "\n")
    else:
        domain_clear = re.sub(r"https://(m\.)?vk\.com/", "", domain)
        domain_stoplist = Path(bot.config["domains"][domain].get(
            filetype,
            bot.config_path.parent / f"{filetype}_{domain_clear}.txt"
        ))
        bot.config["domains"][domain][filetype] = str(domain_stoplist)
        with domain_stoplist.open("a", encoding="utf-8") as f:
            f.write(message.text + "\n")
    bot.save_config()


@AutoPoster.on_message(pyrogram.filters.forwarded & pyrogram.filters.private)
def get_forward_id(_, message: Message):
    if message.forward_from:
        id_ = message.forward_from.id
    elif message.forward_from_chat:
        id_ = message.forward_from_chat.id
    else:
        id_ = "hidden"
    message.reply("Channel (user) ID is `{}`".format(id_))
