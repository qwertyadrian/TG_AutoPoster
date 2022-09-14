import urllib.error
from re import IGNORECASE, MULTILINE, sub

from bs4 import BeautifulSoup
from loguru import logger
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                            InputMediaAudio, InputMediaDocument,
                            InputMediaPhoto, InputMediaVideo)
from vk_api import VkApi, exceptions
from vk_api.audio import VkAudio
from wget import download

from ..tools import build_menu, split
from .tools import Attachments, add_audio_tags, download_video, start_process

MAX_FILENAME_LENGTH = 255
DOMAIN_REGEX = r"https://(m\.)?vk\.com/"


class Post:
    def __init__(
        self,
        post: dict,
        domain: str,
        session: VkApi,
        sign_posts: bool = False,
        what_to_parse: set = None,
        header: str = "",
        footer: str = "",
    ):
        self.session = session
        try:
            self.audio_session = VkAudio(session)
        except IndexError:
            self.audio_session = None
        self.sign_posts = sign_posts
        self.pattern = "@" + sub(DOMAIN_REGEX, "", domain)
        self.raw_post = post
        self.post_url = "https://vk.com/wall{owner_id}_{id}".format(
            **self.raw_post
        )
        self.text = ""
        self.repost = None
        self.repost_source = None
        self.reply_markup = None
        self.attachments = Attachments()
        self.poll = None
        self.what_to_parse = what_to_parse
        self.header = header
        self.footer = footer

    def parse_post(self):
        logger.info("[VK] Парсинг поста.")
        if self.what_to_parse.intersection({"text", "all"}):
            self.parse_text()

        if "attachments" in self.raw_post:
            for attachment in self.raw_post["attachments"]:
                if attachment["type"] in (
                    "link",
                    "page",
                    "album",
                ) and self.what_to_parse.intersection({"link", "all"}):
                    self.parse_link(attachment)
                if attachment[
                    "type"
                ] == "photo" and self.what_to_parse.intersection(
                    {"photo", "all"}
                ):
                    self.parse_photo(attachment["photo"])
                if attachment[
                    "type"
                ] == "video" and self.what_to_parse.intersection(
                    {"video", "all"}
                ):
                    self.parse_video(attachment["video"])
                if attachment[
                    "type"
                ] == "doc" and self.what_to_parse.intersection({"doc", "all"}):
                    self.parse_doc(attachment["doc"])
                if attachment[
                    "type"
                ] == "poll" and self.what_to_parse.intersection(
                    {"polls", "all"}
                ):
                    self.parse_poll(attachment["poll"])
                if attachment[
                    "type"
                ] == "audio" and self.what_to_parse.intersection(
                    {"music", "all"}
                ):
                    self.parse_music(attachment["audio"])

        if self.sign_posts:
            self.sign_post()

        self.text = "{}\n\n{}\n{}".format(self.header, self.text, self.footer)
        self.text = split(self.text.strip())

    def parse_text(self):
        if self.raw_post["text"]:
            logger.info("[VK] Обнаружен текст. Извлечение.")
            self.text += self.raw_post["text"].strip()
            if self.pattern != "@":
                self.text = sub(self.pattern, "", self.text, flags=IGNORECASE)
            self.text = (
                self.text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            self.text = sub(
                r"\[((https://)?vk\.com/)?(.*?)\|(.*?)\]",
                self.link_sub,
                self.text,
            )
            self.text = sub(
                r"<a(.*?)><(.*?)/a>", "", self.text, flags=MULTILINE
            )
            self.text += "\n"

    def parse_link(self, attachment):
        logger.info("[VK] Парсинг ссылки")
        logger.debug(attachment)
        if attachment[attachment["type"]]["title"] == self.text.strip():
            self.text = ""
        if attachment["type"] == "link" and attachment["link"]["title"]:
            self.text += '\n🔗 <a href="{url}">{title}</a>'.format(
                **attachment["link"]
            )
            if attachment["link"].get("product"):
                self.text += "\nЦена: {}".format(
                    attachment["link"]["product"]["price"]["text"]
                )
        elif attachment["type"] == "page":
            self.text += '\n🔗 <a href="{view_url}">{title}</a>\n👁 {views} раз(а)'.format(
                **attachment["page"]
            )
        elif attachment["type"] == "album":
            self.text += (
                '\n🖼 <a href="https://vk.com/album{owner_id}_{id}">'
                "Альбом с фотографиями: {title}</a>\n"
                "Описание: {description}".format(**attachment["album"])
            )

    def parse_photo(self, attachment):
        logger.info("[VK] Извлечение фото")
        logger.debug(attachment)
        photo = None
        max_width = 0
        for i in attachment["sizes"]:
            if i["width"] > max_width:
                photo = i["url"]
                max_width = i["width"]
        photo = download(photo, bar=None)
        if photo:
            self.attachments.media.append(InputMediaPhoto(photo))

    def parse_doc(self, attachment):
        logger.info("[VK] Извлечение документа {}", attachment["title"])
        logger.debug(attachment)
        try:
            attachment["title"] = sub(
                r"[/\\:*?\"><|]", "", attachment["title"]
            )
            if attachment["title"].endswith(attachment["ext"]):
                doc = download(
                    attachment["url"], out="{title}".format(**attachment)
                )
            else:
                doc = download(
                    attachment["url"], out="{title}.{ext}".format(**attachment)
                )
            self.attachments.documents.append(InputMediaDocument(doc))
        except urllib.error.URLError as error:
            logger.exception(
                "[VK] Невозможно скачать вложенный файл: {0}.", error
            )
            self.text += '\n📃 <a href="{url}">{title}</a>'.format(**attachment)

    def parse_video(self, attachment):
        logger.info("[VK] Извлечение видео")
        logger.debug(attachment)

        video_link = "https://m.vk.com/video{owner_id}_{id}".format(
            **attachment
        )
        soup = BeautifulSoup(
            self.session.http.get(video_link).text, "html.parser"
        )

        if (
            not attachment.get("platform")
            and len(soup.find_all("source")) >= 2
        ):
            video_link = soup.find_all("source")[1].get("src")
            filesize = self.session.http.head(video_link).headers[
                "Content-Length"
            ]
            if int(filesize) >= 2 * 10**9:
                logger.info(
                    "[VK] Видео весит более 2 ГБ. Добавляем ссылку на видео в текст."
                )
                self.text += '\n🎥 <a href="{0}">{1[title]}</a>\n👁 {1[views]} раз(а) ⏳ {1[duration]} сек'.format(
                    video_link.replace("m.", ""), attachment
                )
                return None
            else:
                file = download_video(self.session.http, video_link)
            self.attachments.media.append(InputMediaVideo(file))
        else:
            video = self.session.method(
                method="video.get",
                values={
                    "owner_id": attachment["owner_id"],
                    "videos": "{owner_id}_{id}".format(**attachment),
                },
            )["items"]
            if video:
                video_link = (
                    video[0].get("files", {}).get("external", video_link)
                )
            self.text += '\n🎥 <a href="{0}">{1[title]}</a>\n👁 {1[views]} раз(а) ⏳ {1[duration]} сек'.format(
                video_link.replace("m.", ""), attachment
            )

    def parse_music(self, attachment):
        logger.info(
            "[VK] Извлечение аудио {} - {}",
            attachment["artist"],
            attachment["title"],
        )
        logger.debug(attachment)
        if not attachment.get("url") or attachment.get("url", "").endswith(
            "audio_api_unavailable.mp3"
        ):
            try:
                track = self.audio_session.get_audio_by_id(
                    attachment["owner_id"], attachment["id"]
                )
            except (ValueError, AttributeError):
                logger.warning(
                    "[VK] Unable to get audio link. Attempt using official VK API"
                )
                try:
                    track = self.session.method(
                        method="audio.getById",
                        values={
                            "audios": "{owner_id}_{id}".format(**attachment)
                        },
                    )[0]
                except exceptions.ApiError:
                    logger.warning(
                        "[VK] Аудиозапись недоступна для скачивания"
                    )
                    return
        else:
            track = attachment
        name = (
            sub(
                r"[^a-zA-Z '#0-9.а-яА-Я()-]",
                "",
                track["artist"] + " - " + track["title"],
            )[: MAX_FILENAME_LENGTH - 16]
            + ".mp3"
        )
        track_cover = None
        if ".m3u8" in track["url"]:
            logger.warning("[VK] Файлом аудиозаписи является m3u8 плейлист.")
            file = name
            streamlink_args = [
                "streamlink",
                "--output",
                name.replace(".mp3", ".ts"),
                track["url"],
                "best",
            ]
            ffmpeg_args = [
                "ffmpeg",
                "-i",
                name.replace(".mp3", ".ts"),
                "-b:a",
                "320k",
                name,
            ]

            result = start_process(streamlink_args)
            if result > 0:
                logger.critical(
                    "[VK] При запуске команды {} произошла ошибка.",
                    " ".join(streamlink_args),
                )
                return

            result = start_process(ffmpeg_args)
            if result > 0:
                logger.critical(
                    "[VK] При запуске команды {} произошла ошибка",
                    " ".join(ffmpeg_args),
                )
                return
        else:
            try:
                file = download(track["url"], out=name)
            except (urllib.error.URLError, IndexError, ValueError):
                logger.exception(
                    "[VK] Не удалось скачать аудиозапись. Пропускаем ее"
                )
                return
        if track.get("album"):
            if track["album"].get("thumb"):
                for key in track["album"]["thumb"]:
                    if key.startswith("photo"):
                        track_cover = download(
                            track["album"]["thumb"][key].replace("impf/", ""),
                            bar=None,
                        )
        logger.debug("Adding tags in track")
        result = add_audio_tags(
            file,
            title=track["title"],
            artist=track["artist"],
            track_cover=track_cover,
        )
        if result:
            logger.debug("Track {} ready for sending", name)
            self.attachments.audio.append(
                InputMediaAudio(
                    name,
                    track_cover,
                    duration=track["duration"],
                    performer=track["artist"],
                    title=track["title"],
                )
            )

    def parse_poll(self, attachment):
        logger.info("[VK] Извлечение опроса")
        logger.debug(attachment)
        self.poll = {
            "question": attachment["question"],
            "options": [answer["text"] for answer in attachment["answers"]],
            "allows_multiple_answers": attachment["multiple"],
            "is_anonymous": attachment["anonymous"],
        }
        if len(self.poll["options"]) == 1:
            self.poll["options"].append("...")

    @staticmethod
    def link_sub(match):
        if match.group(3).startswith("https:"):
            return "<a href='{2}'>{3}</a>".format(*match.groups())
        return "<a href='https://vk.com/{2}'>{3}</a>".format(*match.groups())

    def sign_post(self):
        button_list = []
        logger.info(
            "[VK] Подписывание поста и добавление ссылки на его оригинал."
        )
        user = self.parse_user()
        if len(self.attachments.media) > 1:
            if user:
                self.text += '\nАвтор поста: <a href="https://vk.com/{domain}">{first_name} {last_name}</a>'.format(
                    user, **user
                )
            self.text += '\n<a href="{}">Оригинал поста</a>'.format(
                self.post_url
            )
            if self.raw_post.get("copyright"):
                self.text += '\nИсточник: <a href="{link}">{name}</a>'.format(
                    **self.raw_post["copyright"]
                )
        else:
            if user:
                button_list.append(
                    InlineKeyboardButton(
                        "Автор поста: {first_name} {last_name}".format(**user),
                        url="https://vk.com/{0[domain]}".format(user),
                    )
                )
            button_list.append(
                InlineKeyboardButton("Оригинал поста", url=self.post_url)
            )
            if self.raw_post.get("copyright"):
                button_list.append(
                    InlineKeyboardButton(
                        "Источник: {name}".format(
                            **self.raw_post["copyright"]
                        ),
                        url=self.raw_post["copyright"]["link"],
                    )
                )
        self.reply_markup = (
            InlineKeyboardMarkup(build_menu(button_list))
            if button_list
            else None
        )

    def parse_user(self):
        logger.info("[VK] Получение информации об авторе поста")
        user = None
        if "signer_id" in self.raw_post:
            user = self.session.method(
                method="users.get",
                values={
                    "user_ids": self.raw_post["signer_id"],
                    "fields": "domain",
                },
            )[0]
        elif self.raw_post["owner_id"] != self.raw_post["from_id"]:
            user = self.session.method(
                method="users.get",
                values={
                    "user_ids": self.raw_post["from_id"],
                    "fields": "domain",
                },
            )[0]
        return user

    def parse_repost(self):
        logger.info(
            "[VK] Включена отправка репостов. Начинаем парсинг репоста"
        )
        source_id = int(self.raw_post["copy_history"][0]["from_id"])
        try:
            source_info = self.session.method(
                method="groups.getById", values={"group_id": -source_id}
            )[0]
            repost_source = 'Репост из <a href="https://vk.com/{screen_name}">{name}</a>:\n\n'.format(
                **source_info
            )
        except exceptions.ApiError:
            source_info = self.session.method(
                method="users.get", values={"user_ids": source_id}
            )[0]
            repost_source = 'Репост от <a href="https://vk.com/id{id}">{first_name} {last_name}</a>:\n\n'.format(
                **source_info
            )
        self.repost = Post(
            self.raw_post["copy_history"][0],
            source_info.get("screen_name", ""),
            self.session,
            self.sign_posts,
            self.what_to_parse,
        )
        self.repost.parse_post()
        self.repost.text = split(repost_source + " ".join(self.repost.text))

    def __bool__(self):
        return (
            bool("".join(self.text))
            or bool(self.attachments)
            or bool(self.poll)
        )


class Story:
    def __init__(self, story=None):
        self.story = story
        self.text = [""]
        self.attachments = Attachments()
        self.reply_markup = None

    def __bool__(self):
        return bool(self.story)

    def parse_story(self):
        if self.story["type"] == "photo":
            self.parse_photo()
        elif self.story["type"] == "video":
            self.parse_video()
        if self.story.get("link"):
            self.parse_link()

    def parse_photo(self):
        logger.info("[VK] Извлечение фото...")
        photo = None
        for i in self.story["photo"]["sizes"]:
            photo = i["url"]
        photo = download(photo, bar=None)
        if photo is not None:
            self.attachments.media.append(InputMediaPhoto(photo))

    def parse_video(self):
        logger.info("[VK] Извлечение видео")
        video_link = None
        video_file = None
        for _, v in self.story["video"]["files"].items():
            video_link = v
        if video_link is not None:
            video_file = download(video_link)
        if video_file is not None:
            self.attachments.media.append(InputMediaVideo(video_file))

    def parse_link(self):
        logger.info("[AP] Обнаружена ссылка, создание кнопки")
        button_list = [InlineKeyboardButton(**self.story["link"])]
        self.reply_markup = InlineKeyboardMarkup(
            build_menu(button_list, n_cols=2)
        )
