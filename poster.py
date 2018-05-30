import sys
import time
from os import remove
from os.path import getsize
from botlogs import log
from settings import config, api_vk, update_parameter
from classes import Post


def get_data(group):
    """
    Функция получения новых постов с серверов VK. В случае успеха возвращает словарь с постами, а в случае неудачи -
    ничего

    :param group: ID группы ВК
    :return: Возвращает словарь с постами
    """
    # noinspection PyBroadException
    try:
        feed = api_vk.wall.get(domain=group, count=11)
        return feed['items']
    except Exception:
        log.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None


def updater(bot, domain, last_id):
    posts = get_data(domain)
    for post in reversed(posts):
        if post['id'] > last_id:
            log.info("New post found with id = %s and %s symbols." % (post['id'], len(post['text'])))
            new_post = Post(post, domain)
            new_post.generate_post()
            send_post(bot, domain, new_post)
            last_id = update_parameter(domain, 'last_id', post['id'])
            time.sleep(5)
    log.info('Finished updater, last_id = %s.' % last_id)


def send_post(bot, domain, post):
    log.info("Sending post...")
    if post.text:
        if not (len(post.photos) == 1 and len(post.text) < 200):
            bot.sendMessage(chat_id=config.get(domain, 'channel'), text=post.text, parse_mode='Markdown',
                            disable_web_page_preview=True)
    if post.photos:
        try:
            if post.text:
                if len(post.photos) == 1 and len(post.text) < 200:
                    bot.sendPhoto(chat_id=config.get(domain, 'channel'), photo=post.photos[0]['media'],
                                  caption=post.text)
                else:
                    bot.sendMediaGroup(chat_id=config.get(domain, 'channel'), media=post.photos)
            else:
                bot.sendMediaGroup(chat_id=config.get(domain, 'channel'), media=post.photos)
        except Exception:
            log.warning('Could not send photos: %s.' % sys.exc_info()[0])
    for m in post.videos:
        bot.sendMessage(config.get(domain, 'channel'), m)
    for m in post.docs:
        bot.sendDocument(chat_id=config.get(domain, 'channel'), document=open(m, 'rb'))
    for m in post.tracks:
        try:
            if getsize(m) > 52428800:
                remove(m)
            else:
                bot.sendAudio(chat_id=config.get(domain, 'channel'), audio=open(m, 'rb'))
            remove(m)
        except FileNotFoundError:
            continue
