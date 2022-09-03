import re
import time
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Union

from loguru import logger
from vk_api import VkApi

from .parser import Post, Story

DOMAIN_REGEX = r"https://(m\.)?vk\.com/"


class Group:
    def __init__(
        self,
        domain: str,
        session: VkApi,
        last_id: int = 0,
        last_story_id: int = 0,
        pinned_id: int = 0,
        sign_posts: bool = True,
        send_reposts: Union[bool, str] = False,
        send_stories: bool = False,
        what_to_send: Sequence[str] = None,
        posts_count: int = 11,
        stop_list: str = "",
        blacklist: str = "",
        header: str = "",
        footer: str = "",
        **kwargs,
    ):
        self.domain = str(domain)
        self._session = session
        self.last_id = last_id
        self.last_story_id = last_story_id
        self.pinned_id = pinned_id
        self.sign_posts = sign_posts
        self.send_reposts = send_reposts
        self.send_stories = send_stories
        self.what_to_parse = set(what_to_send) if what_to_send else {"all"}
        self.posts_count = posts_count
        self.header = header
        self.footer = footer

        self.stop_list = Path(stop_list)
        if self.stop_list.is_file():
            self.stop_list = list(
                filter(
                    lambda x: bool(x),
                    self.stop_list.read_text(encoding="utf-8").split("\n")
                )
            )
        else:
            self.stop_list = []

        self.blacklist = Path(blacklist)
        if self.blacklist.is_file():
            self.blacklist = list(
                filter(
                    lambda x: bool(x),
                    self.blacklist.read_text(encoding="utf-8").split("\n")
                )
            )
        else:
            self.blacklist = []

    def get_posts(self) -> Iterable[Union[Post, None]]:
        logger.info(
            "[VK] Проверка на наличие новых постов в {} с последним ID {}",
            self.domain,
            self.last_id,
        )
        if self.posts_count > 100:
            logger.warning(
                "[VK] Проверяется более 100 постов за раз. "
                "После проверки рекомендуется уменьшить значение posts_count до 100 или меньше."
            )
            total = self.get_raw_posts(1)["count"]
            offset = min(self.posts_count, total)
            while offset > 0:
                posts = self.get_raw_posts(100, offset)["items"]
                for post in reversed(posts):
                    yield from self.get_post(post)
                offset -= min(100, offset)
            else:
                posts = self.get_raw_posts(100, offset)["items"]
                for post in reversed(posts):
                    yield from self.get_post(post)
        else:
            posts = self.get_raw_posts(self.posts_count)["items"]
            for post in reversed(posts):
                yield from self.get_post(post)

    def get_post(self, post) -> Iterable[Union[Post, None]]:
        is_pinned = post.get("is_pinned", False)
        if post["id"] > self.last_id or (
            is_pinned and post["id"] != self.pinned_id
        ):
            logger.info("[VK] Обнаружен новый пост с ID {}", post["id"])
            if post.get("marked_as_ads", 0):
                logger.info("[VK] Пост рекламный. Он будет пропущен.")
                return
            for word in self.stop_list:
                if word.lower() in post["text"].lower():
                    break
            else:
                for word in self.blacklist:
                    post["text"] = re.sub(
                        word, "", post["text"], flags=re.MULTILINE
                    )
                parsed_post = Post(
                    post,
                    self.domain,
                    self._session,
                    self.sign_posts,
                    self.what_to_parse,
                    self.header,
                    self.footer
                )
                parsed_post.parse_post()
                self.update_ids(is_pinned, post["id"])
                if "copy_history" in parsed_post.raw_post:
                    logger.info("[VK] В посте содержится репост.")
                    if self.send_reposts == "post_only":
                        logger.info("[VK] Отправка поста без репоста.")
                        yield parsed_post
                    elif not self.send_reposts:
                        logger.info(
                            "[VK] Отправка репостов полностью отключена, поэтому пост будет пропущен."
                        )
                        yield None
                    elif self.send_reposts:
                        yield parsed_post
                        parsed_post.parse_repost()
                        yield parsed_post.repost
                else:
                    yield parsed_post
                time.sleep(5)

    def get_stories(self) -> Iterable[Story]:
        if not self.send_stories:
            return Story()
        logger.info(
            "[VK] Проверка на наличие новых историй в {} с последним ID {}",
            self.domain,
            self.last_story_id,
        )
        stories = self.get_raw_stories()
        for story in reversed(stories):
            if story["id"] > self.last_story_id:
                logger.info(
                    "[VK] Обнаружен новая история с ID {}", story["id"]
                )
                parsed_story = Story(story)
                parsed_story.parse_story()
                self.last_story_id = story["id"]
                if (
                    not story.get("is_expired")
                    and not story.get("is_deleted")
                    and story.get("can_see")
                ):
                    yield parsed_story

    def get_raw_posts(self, count: int = 11, offset: int = 0) -> Dict:
        try:
            feed = self._session.method(
                method="wall.get",
                values={
                    "owner_id": self.group_id,
                    "count": count,
                    "offset": offset,
                },
            )
            return feed
        except Exception as error:
            logger.exception("[VK] Ошибка получения постов: {}", error)
            return dict()

    def get_raw_stories(self) -> List:
        try:
            stories = self._session.method(
                method="stories.get", values={"owner_id": self.group_id}
            )
            return (
                stories["items"][0]["stories"]
                if stories["count"] >= 1
                else list()
            )
        except Exception as error:
            logger.error("[VK] Ошибка получения историй: {}", error)
            return list()

    @property
    def group_id(self):
        group = re.sub(DOMAIN_REGEX, "", self.domain)
        if (
            group.startswith("club")
            or group.startswith("public")
            or "-" in group
        ):
            group = group.replace("club", "-").replace("public", "-")
        elif group.startswith("id"):
            group = group.replace("id", "")
        else:
            group = -self._session.method(
                method="groups.getById", values={"group_id": group}
            )[0]["id"]
        return int(group)

    def update_ids(self, is_pinned, post_id):
        if is_pinned:
            self.pinned_id = post_id
        if post_id > self.last_id:
            self.last_id = post_id
