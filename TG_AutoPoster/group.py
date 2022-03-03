import re
import time
from typing import Iterable, List

from loguru import logger as log
from vk_api import VkApi

from .parser import VkPostParser, VkStoryParser

DOMAIN_REGEX = r"https://(m\.)?vk\.com/"


class Group:
    def __init__(
        self,
        domain: str,
        vk_session: VkApi,
        last_id: int = 0,
        pinned_id: int = 0,
        send_reposts: int = 0,
        sign_posts: bool = True,
        what_to_parse: set = None,
        posts_count: int = 11,
        last_story_id: int = 0,
    ):
        self.domain = domain
        self.send_reposts = send_reposts
        self.sign_posts = sign_posts
        self.what_to_parse = what_to_parse if what_to_parse else {"all"}
        self.posts_count = posts_count
        self.last_id = last_id
        self.pinned_id = pinned_id
        self.last_story_id = last_story_id
        self._vk_session = vk_session

    def get_posts(self) -> Iterable[VkPostParser]:
        posts = self.get_raw_posts()
        for post in reversed(posts):
            is_pinned = post.get("is_pinned", False)
            if post["id"] > self.last_id or (is_pinned and post["id"] != self.pinned_id):
                log.info("[VK] Обнаружен новый пост с ID {}", post["id"])
                if post.get("marked_as_ads", 0):
                    log.info("[VK] Пост рекламный. Он будет пропущен.")
                    continue
                parsed_post = VkPostParser(post, self.domain, self._vk_session, self.sign_posts, self.what_to_parse)
                parsed_post.generate_post()
                self.update_ids(is_pinned, post["id"])
                if "copy_history" in parsed_post.raw_post:
                    log.info("В посте содержится репост.")
                    if self.send_reposts in ("no", 0):
                        log.info("Отправка репостов полностью отключена, поэтому пост будет пропущен.")
                    elif self.send_reposts in ("post_only", 1):
                        log.info("Отправка поста без репоста.")
                        yield parsed_post
                    elif self.send_reposts in ("yes", "all", 2):
                        yield parsed_post
                        parsed_post.generate_repost()
                        yield parsed_post.repost
                else:
                    yield parsed_post
                time.sleep(5)

    def get_stories(self) -> Iterable[VkStoryParser]:
        log.info("[VK] Проверка на наличие новых историй в {} с последним ID {}", self.domain, self.last_story_id)
        stories = self.get_raw_stories()
        for story in reversed(stories):
            if story["id"] > self.last_story_id:
                log.info("[VK] Обнаружен новая история с ID {}", story["id"])
                parsed_story = VkStoryParser(story)
                parsed_story.generate_story()
                self.last_story_id = story["id"]
                if not story.get("is_expired") and not story.get("is_deleted") and story.get("can_see"):
                    yield parsed_story

    def get_raw_posts(self) -> List:
        try:
            log.info("Получение последних {} постов", self.posts_count)
            group = re.sub(DOMAIN_REGEX, "", self.domain)
            if group.startswith("club") or group.startswith("public") or "-" in group:
                group = group.replace("club", "-").replace("public", "-")
                feed = self._vk_session.method(method="wall.get", values={"owner_id": group, "count": self.posts_count})
            else:
                feed = self._vk_session.method(method="wall.get", values={"domain": group, "count": self.posts_count})
            return feed["items"]
        except Exception as error:
            log.exception("Ошибка получения постов: {}", error)
            return list()

    def get_raw_stories(self) -> List:
        try:
            group = re.sub(DOMAIN_REGEX, "", self.domain)
            if group.startswith("club") or group.startswith("public") or "-" in group:
                group = group.replace("club", "-").replace("public", "-")
            elif group.startswith("id"):
                group = group.replace("id", "")
            else:
                group = -self._vk_session.method(method="groups.getById", values={"group_ids": group})[0]["id"]
            stories = self._vk_session.method(method="stories.get", values={"owner_id": group})
            return stories["items"][0]["stories"] if stories["count"] >= 1 else list()
        except Exception as error:
            log.error("Ошибка получения историй: {}", error)
            return list()

    def update_ids(self, is_pinned, post_id):
        if is_pinned:
            self.pinned_id = post_id
        if post_id > self.last_id:
            self.last_id = post_id
