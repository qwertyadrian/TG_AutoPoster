from typing import Sequence, Union

import pyrogram.errors
from loguru import logger
from pyrogram import Client
from pyrogram.types import (InputMediaAudio, InputMediaDocument,
                            InputMediaPhoto, InputMediaVideo)

from ..tools import timeout_handler
from .parser import Post


class Sender:
    def __init__(
        self,
        bot: Client,
        post: Post,
        chat_ids: Sequence[Union[int, str]],
        disable_notification: bool = False,
        disable_web_page_preview: bool = True,
        **kwargs,
    ):
        self._bot = bot
        self.post = post
        self.chat_ids = chat_ids
        self.disable_notification = disable_notification
        self.disable_web_page_preview = disable_web_page_preview

    @logger.catch(reraise=True)
    def send_post(self):
        for chat_id in self.chat_ids:
            self.send_splitted_message(self.post.text, chat_id)
            if (
                len(self.post.text) >= 1
                and len(self.post.text[-1]) >= 1024
                or len(self.post.attachments) == 0
                and bool(self.post.text[-1])
            ):
                message = timeout_handler(self._bot.send_message)(
                    chat_id,
                    self.post.text[-1],
                    reply_markup=self.post.reply_markup
                    if len(self.post.attachments) == 0
                    else None,
                    disable_web_page_preview=self.disable_web_page_preview,
                    disable_notification=self.disable_notification,
                )
                caption = ""
                msg_id = message.id
            else:
                caption = self.post.text[-1]
                msg_id = None

            if self.send_attachments(
                chat_id, self.post.attachments["media"], caption, msg_id
            ):
                caption = ""
            if self.send_attachments(
                chat_id, self.post.attachments["docs"], caption, msg_id
            ):
                caption = ""
            self.send_attachments(
                chat_id, self.post.attachments["audio"], caption, msg_id
            )

            if hasattr(self.post, "poll") and self.post.poll:
                self.send_poll(chat_id)

    @timeout_handler
    def send_attachments(self, chat_id, attachments, caption, msg_id):
        if len(attachments) == 0:
            return False
        elif len(attachments) == 1:
            attachment = attachments[0]
            if isinstance(attachment, InputMediaPhoto):
                self._bot.send_photo(
                    chat_id,
                    attachment.media,
                    caption=caption,
                    reply_markup=self.post.reply_markup,
                    disable_notification=self.disable_notification,
                    reply_to_message_id=msg_id,
                )
            elif isinstance(attachment, InputMediaVideo):
                self._bot.send_video(
                    chat_id,
                    attachment.media,
                    caption=caption,
                    reply_markup=self.post.reply_markup,
                    disable_notification=self.disable_notification,
                    reply_to_message_id=msg_id,
                )
            elif isinstance(attachment, InputMediaDocument):
                self._bot.send_document(
                    chat_id,
                    document=attachment.media,
                    caption=caption,
                    disable_notification=self.disable_notification,
                    reply_to_message_id=msg_id,
                )
            elif isinstance(attachment, InputMediaAudio):
                self._bot.send_audio(
                    chat_id,
                    attachment.media,
                    thumb=attachment.thumb,
                    duration=attachment.duration,
                    title=attachment.title,
                    performer=attachment.performer,
                    caption=caption,
                    disable_notification=self.disable_notification,
                    reply_to_message_id=msg_id,
                )
        else:
            attachments[0].caption = caption
            try:
                self._bot.send_media_group(
                    chat_id,
                    media=attachments,
                    disable_notification=self.disable_notification,
                    reply_to_message_id=msg_id,
                )
            except pyrogram.errors.MediaEmpty:
                for doc in attachments:
                    self._bot.send_document(
                        chat_id,
                        document=doc.media,
                        caption=doc.caption,
                        disable_notification=self.disable_notification,
                        reply_to_message_id=msg_id,
                        reply_markup=self.post.reply_markup,
                    )
                    self.post.reply_markup = None
        return True

    @timeout_handler
    def send_poll(self, chat_id):
        logger.info("Отправка опроса")
        try:
            self._bot.send_poll(
                chat_id,
                **self.post.poll,
                disable_notification=self.disable_notification,
            )
        except pyrogram.errors.BroadcastPublicVotersForbidden:
            logger.critical(
                "Отправка публичных опросов в каналы запрещена. Отправка анонимного опроса"
            )
            self.post.poll["is_anonymous"] = True
            self._bot.send_poll(
                chat_id,
                **self.post.poll,
                disable_notification=self.disable_notification,
            )

    @timeout_handler
    def send_splitted_message(self, text, chat_id):
        for i in range(len(text) - 1):
            self._bot.send_message(
                chat_id,
                text[i],
                disable_notification=self.disable_notification,
            )
