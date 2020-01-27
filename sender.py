import telegram.error
from loguru import logger as log

from tools import list_splitter, split


class PostSender:
    def __init__(self, bot, post, chat_id, disable_notification=False):
        self.bot = bot
        self.post = post
        self.chat_id = chat_id
        self.text = split(self.post.text)
        self.disable_notification = disable_notification

    @log.catch()
    def send_post(self):
        try:
            self.send_text_and_photos()
            if hasattr(self.post, "videos") and len(self.post.videos) != 0:
                self.send_videos()
            if hasattr(self.post, "docs") and len(self.post.docs) != 0:
                self.send_documents()
            if hasattr(self.post, "tracks") and len(self.post.tracks) != 0:
                self.send_music()
            if hasattr(self.post, "poll") and self.post.poll:
                self.send_poll()
        except telegram.error.BadRequest as error:
            if str(error) == "Chat not found":
                log.error(
                    "Чат {} не был найден. Возможно, ID чата (канала) указан неверно или бот отсутствует в нём.".format(
                        self.chat_id
                    )
                )
            else:
                log.error("Bad Request: {}".format(str(error)))
        except telegram.error.TimedOut:
            log.error("Timed out: время ожидания истекло.")
        except telegram.error.TelegramError as error:
            log.error("Telegram Error: {}".format(str(error)))

    def send_text_and_photos(self):
        if self.post.photos:
            if len(self.post.photos) == 1:
                log.info("Отправка текста и фото")
                if len(self.post.text) > 1024:
                    self.send_splitted_message(self.bot, self.text, self.chat_id)
                    self.bot.send_message(
                        self.chat_id,
                        self.text[-1],
                        parse_mode="HTML",
                        reply_markup=self.post.reply_markup,
                        disable_web_page_preview=True,
                        disable_notification=self.disable_notification,
                    )
                    self.bot.send_photo(
                        self.chat_id,
                        self.post.photos[0]["media"],
                        parse_mode="HTML",
                        disable_notification=self.disable_notification,
                    )
                else:
                    self.bot.send_photo(
                        self.chat_id,
                        self.post.photos[0]["media"],
                        caption=self.text[-1],
                        reply_markup=self.post.reply_markup,
                        parse_mode="HTML",
                        disable_notification=self.disable_notification,
                    )
            else:
                log.info("Отправка текста")
                if len(self.post.text) > 1024:
                    self.send_splitted_message(self.bot, self.text, self.chat_id)
                    self.bot.send_message(
                        self.chat_id,
                        self.text[-1],
                        parse_mode="HTML",
                        reply_markup=self.post.reply_markup,
                        disable_web_page_preview=True,
                        disable_notification=self.disable_notification,
                    )
                    for i in list_splitter(self.post.photos, 10):
                        self.bot.send_media_group(self.chat_id, i, disable_notification=self.disable_notification)
                else:
                    for i in list_splitter(self.post.photos, 10):
                        self.bot.send_media_group(
                            self.chat_id,
                            i,
                            reply_markup=self.post.reply_markup,
                            disable_notification=self.disable_notification,
                        )
        elif self.post.text and not self.post.photos and not self.post.videos and not self.post.docs:
            self.send_splitted_message(self.bot, self.text, self.chat_id)
            self.bot.send_message(
                self.chat_id,
                self.text[-1],
                parse_mode="HTML",
                reply_markup=self.post.reply_markup,
                disable_web_page_preview=True,
                disable_notification=self.disable_notification,
            )

    def send_videos(self):
        log.info("Отправка видео")
        for i, video in enumerate(self.post.videos):
            if i == 0:
                if not self.post.photos:
                    if len(self.post.text) < 1024:
                        self.bot.send_video(
                            self.chat_id,
                            video=open(video, "rb"),
                            timeout=60,
                            parse_mode="HTML",
                            caption=self.text[-1],
                            reply_markup=self.post.reply_markup,
                            disable_notification=self.disable_notification,
                        )
                    else:
                        self.send_splitted_message(self.bot, self.text, self.chat_id)
                        self.bot.send_message(
                            self.chat_id,
                            self.text[-1],
                            parse_mode="HTML",
                            reply_markup=self.post.reply_markup,
                            disable_web_page_preview=True,
                            disable_notification=self.disable_notification,
                        )
                        self.bot.send_video(
                            self.chat_id,
                            video=open(video, "rb"),
                            disable_notification=self.disable_notification,
                            timeout=60,
                        )
                else:
                    self.bot.send_video(
                        self.chat_id,
                        video=open(video, "rb"),
                        disable_notification=self.disable_notification,
                        timeout=60,
                    )
            else:
                self.bot.send_video(
                    self.chat_id, video=open(video, "rb"), disable_notification=self.disable_notification, timeout=60,
                )

    def send_documents(self):
        log.info("Отправка прочих вложений")
        for i, (doc, filename) in enumerate(self.post.docs):
            if i == 0:
                if not self.post.photos and not self.post.videos:
                    if len(self.post.text) < 1024:
                        self.bot.send_document(
                            self.chat_id,
                            document=open(doc, "rb"),
                            caption=self.text[-1],
                            parse_mode="HTML",
                            timeout=60,
                            reply_markup=self.post.reply_markup,
                            disable_notification=self.disable_notification,
                        )
                    else:
                        self.send_splitted_message(self.bot, self.text, self.chat_id)

                        self.bot.send_message(
                            self.chat_id,
                            self.text[-1],
                            parse_mode="HTML",
                            reply_markup=self.post.reply_markup,
                            disable_web_page_preview=True,
                            disable_notification=self.disable_notification,
                        )

                        self.bot.send_document(
                            self.chat_id,
                            document=open(doc, "rb"),
                            disable_notification=self.disable_notification,
                            timeout=60,
                        )
                else:
                    self.bot.send_document(
                        self.chat_id,
                        document=open(doc, "rb"),
                        disable_notification=self.disable_notification,
                        timeout=60,
                    )
            else:
                self.bot.send_document(
                    self.chat_id, document=open(doc, "rb"), disable_notification=self.disable_notification, timeout=60,
                )

    def send_music(self):
        log.info("Отправка аудио")
        for audio, duration in self.post.tracks:
            self.bot.send_audio(
                self.chat_id, open(audio, "rb"), duration, disable_notification=self.disable_notification, timeout=60,
            )

    def send_poll(self):
        self.bot.send_poll(self.chat_id, **self.post.poll, disable_notification=self.disable_notification)

    def send_splitted_message(self, bot, text, chat_id):
        for i in range(len(text) - 1):
            bot.send_message(chat_id, text[i], parse_mode="HTML", disable_notification=self.disable_notification)
