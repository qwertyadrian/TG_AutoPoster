from typing import Union

import pyrogram.errors
from loguru import logger as log
from pyrogram import Client
from pyrogram.types import InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo

from .parser import VkPostParser, VkStoryParser
from .tools import split


class PostSender:
    def __init__(
        self,
        bot: Client,
        post: Union[VkPostParser, VkStoryParser],
        chat_id: Union[int, str],
        disable_notification: bool = False,
        disable_web_page_preview: bool = True,
    ):
        self.bot = bot
        self.post = post
        self.chat_id = chat_id
        self.text = self.post.text
        self.splitted_text = split(self.post.text)
        self.disable_notification = disable_notification
        self.disable_web_page_preview = disable_web_page_preview

    @log.catch()
    def send_post(self):
        try:
            self.send_attachments(self.post.media)
            if len(self.post.docs) != 0:
                self.send_attachments(self.post.docs)
            if len(self.post.tracks) != 0:
                self.send_attachments(self.post.tracks)
            if hasattr(self.post, "poll") and self.post.poll:
                self.send_poll()
        except (pyrogram.errors.ChatIdInvalid, pyrogram.errors.PeerIdInvalid):
            log.exception(
                "Чат {} не был найден. Возможно, ID чата (канала) указан неверно или бот отсутствует в нём.".format(
                    self.chat_id
                )
            )
            log.opt(exception=True).debug("Error stacktrace added to the log message")
        except pyrogram.errors.InternalServerError:
            log.exception("Telegram испытывает проблемы. Попробуйте позднее.")
            log.opt(exception=True).debug("Error stacktrace added to the log message")
        except pyrogram.errors.RPCError as error:
            log.exception("Telegram Error: {}", error)
            log.opt(exception=True).debug("Error stacktrace added to the log message")

    def send_attachments(self, attachments):
        if len(attachments) == 0:
            self.send_splitted_message(self.bot, self.splitted_text, self.chat_id)
            self.bot.send_message(
                self.chat_id,
                self.splitted_text[-1],
                reply_markup=self.post.reply_markup,
                disable_web_page_preview=self.disable_web_page_preview,
                disable_notification=self.disable_notification,
            )
        elif len(attachments) == 1:
            if len(self.text) > 1024:
                self.send_splitted_message(self.bot, self.splitted_text, self.chat_id)
                self.bot.send_message(
                    self.chat_id,
                    self.splitted_text[-1],
                    disable_web_page_preview=self.disable_web_page_preview,
                    disable_notification=self.disable_notification,
                )
                self.text = ""
            if isinstance(attachments[0], InputMediaPhoto):
                self.bot.send_photo(
                    self.chat_id,
                    attachments[0].media,
                    caption=self.text,
                    reply_markup=self.post.reply_markup,
                    disable_notification=self.disable_notification,
                )
            elif isinstance(attachments[0], InputMediaVideo):
                self.bot.send_video(
                    self.chat_id,
                    attachments[0].media,
                    caption=self.text,
                    reply_markup=self.post.reply_markup,
                    disable_notification=self.disable_notification,
                )
            elif isinstance(attachments[0], InputMediaDocument):
                self.bot.send_document(
                    self.chat_id,
                    document=attachments[0].media,
                    caption=self.text,
                    disable_notification=self.disable_notification,
                )
            elif isinstance(attachments[0], InputMediaAudio):
                self.bot.send_audio(
                    self.chat_id,
                    attachments[0].media,
                    thumb=attachments[0].thumb,
                    duration=attachments[0].duration,
                    title=attachments[0].title,
                    performer=attachments[0].performer,
                    caption=self.text,
                )
        elif len(attachments) > 1:
            if len(self.text) <= 1024:
                attachments[0].caption = self.text
                self.bot.send_media_group(self.chat_id, attachments, disable_notification=self.disable_notification)
            else:
                self.send_splitted_message(self.bot, self.splitted_text, self.chat_id)
                self.bot.send_message(
                    self.chat_id,
                    self.splitted_text[-1],
                    reply_markup=self.post.reply_markup,
                    disable_web_page_preview=self.disable_web_page_preview,
                    disable_notification=self.disable_notification,
                )
                self.bot.send_media_group(self.chat_id, attachments, disable_notification=self.disable_notification)
        self.text = ""

    def send_poll(self):
        log.info("Отправка опроса")
        try:
            self.bot.send_poll(self.chat_id, **self.post.poll, disable_notification=self.disable_notification)
        except pyrogram.errors.BroadcastPublicVotersForbidden:
            log.exception(
                "Отправка публичных опросов в каналы запрещена. Попытка отправить анонимный опрос."
            )
            self.post.poll["is_anonymous"] = False
            self.bot.send_poll(self.chat_id, **self.post.poll, disable_notification=self.disable_notification)

    def send_splitted_message(self, bot, text, chat_id):
        log.debug("Sending splitted message")
        for i in range(len(text) - 1):
            bot.send_message(chat_id, text[i], disable_notification=self.disable_notification)
