import pyrogram.filters
from pyrogram.types import Message

from .. import AutoPoster
from ..utils.tg import messages

@AutoPoster.on_message()
def update_header_footer(bot: AutoPoster, message: Message):
    if message.from_user.id in bot.conversations.keys():
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


@AutoPoster.on_message(pyrogram.filters.forwarded)
def get_forward_id(_, message: Message):
    if message.forward_from:
        id_ = message.forward_from.id
    else:
        id_ = message.forward_from_chat.id
    message.reply("Channel (user) ID is `{}`".format(id_))