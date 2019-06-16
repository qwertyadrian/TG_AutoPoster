from tools import split
from logger import logger as log


class PostSender:
    def __init__(self, bot, post, chat_id):
        self.bot = bot
        self.post = post
        self.chat_id = chat_id

    def send_post(self):
        self.send_text_and_photos()
        self.send_videos()
        self.send_documents()
        self.send_music()

    @log.catch()
    def send_text_and_photos(self):
        text = split(self.post.text)
        if self.post.text and self.post.photos:
            if len(self.post.photos) > 1:
                send_splitted_message(self.bot, text, self.chat_id)
                self.bot.send_message(self.chat_id, text[-1], parse_mode='HTML', reply_markup=self.post.reply_markup,
                                      disable_web_page_preview=True)
                self.bot.send_media_group(self.chat_id, self.post.photos)
            elif len(self.post.photos) == 1:
                if len(self.post.text) > 1024:
                    send_splitted_message(self.bot, text, self.chat_id)
                    self.bot.send_message(self.chat_id, text[-1], parse_mode='HTML', reply_markup=self.post.reply_markup,
                                          disable_web_page_preview=True)
                    self.bot.send_photo(self.chat_id, self.post.photos[0]['media'], parse_mode='HTML')
                else:
                    send_splitted_message(self.bot, text, self.chat_id)
                    self.bot.send_photo(self.chat_id, self.post.photos[0]['media'], text[-1], parse_mode='HTML',
                                        reply_markup=self.post.reply_markup, disable_web_page_preview=True)
        elif not self.post.text and self.post.photos:
            self.send_photos()
        elif self.post.text and not self.post.photos:
            send_splitted_message(self.bot, text, self.chat_id)
            self.bot.send_message(self.chat_id, text[-1], parse_mode='HTML', reply_markup=self.post.reply_markup,
                                  disable_web_page_preview=True)

    @log.catch()
    def send_photos(self):
        if len(self.post.photos) > 1:
            self.bot.send_media_group(self.chat_id, self.post.photos)
        elif len(self.post.photos) == 1:
            self.bot.send_photo(self.chat_id, self.post.photos[0]['media'], reply_markup=self.post.reply_markup,
                                disable_web_page_preview=True)

    def send_videos(self):
        for video in self.post.videos:
            try:
                self.bot.send_video(self.chat_id, video=open(video, 'rb'), timeout=60)
            except Exception:
                log.exception('Не удалось отправить видео. Пропускаем его...')

    def send_documents(self):
        for doc in self.post.docs:
            try:
                self.bot.send_document(self.chat_id, document=open(doc, 'rb'), timeout=60)
            except Exception:
                log.exception('Не удалось отправить документ. Пропускаем его...')

    def send_music(self):
        for audio, duration in self.post.tracks:
            try:
                self.bot.send_audio(self.chat_id, open(audio, 'rb'), duration, timeout=60)
            except Exception:
                log.exception('Не удалось отправить аудио файл. Пропускаем его...')


def send_splitted_message(bot, text, chat_id):
    for i in range(len(text) - 1):
        bot.send_message(chat_id, text[i], parse_mode='HTML')

