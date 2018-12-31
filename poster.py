import sys
import time
from os import remove
from os.path import getsize
from botlogs import log
from settings import config, api_vk, update_parameter
from classes import Post


def get_data(group: str):
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
        log.error('Ошибка получения информации о новых постах: {0}'.format(sys.exc_info()[0]))
        return None


def updater(bot, domain, last_id):
    log.info('[VK] Проверка на наличие новых постов в {0} с последним ID {1}'.format(domain, last_id))
    posts = get_data(domain)
    for post in reversed(posts):
        if post['id'] > last_id:
            log.info("[VK] Обнаружен новый пост с ID {0}".format(post['id']))
            new_post = Post(post, domain)
            new_post.generate_post()
            send_post(bot, domain, new_post)
            if new_post.repost:
                send_post(bot, domain, new_post.repost)
            last_id = update_parameter(domain, 'last_id', post['id'])
            time.sleep(5)
        if post['id'] == last_id:
            log.info('[VK] Новых постов больше не обнаружено')
    log.info('[VK] Проверка завершена, last_id = {0}.'.format(last_id))


def send_post(bot, domain, post):
    log.info("[TG] Отправка поста...")
    if post.text:
        if post.photos:
            pass
        else:
            try:
                bot.sendMessage(chat_id=config.get(domain, 'channel'), text=post.text, parse_mode='HTML',
                                disable_web_page_preview=True, reply_markup=post.reply_markup)
            except:
                bot.sendMessage(chat_id=config.get(domain, 'channel'), text=post.text,
                                disable_web_page_preview=True, reply_markup=post.reply_markup)
    if post.photos:
        # noinspection PyBroadException
        try:
            if post.text:
                if len(post.photos) == 1 and len(post.text) < 1024:
                    bot.sendPhoto(chat_id=config.get(domain, 'channel'), photo=post.photos[0]['media'],
                                  caption=post.text, parse_mode='HTML', reply_markup=post.reply_markup)
                else:
                    bot.sendMessage(chat_id=config.get(domain, 'channel'), text=post.text, parse_mode='HTML',
                                    disable_web_page_preview=True, reply_markup=post.reply_markup)
                    bot.sendMediaGroup(chat_id=config.get(domain, 'channel'), media=post.photos)
            else:
                bot.sendMediaGroup(chat_id=config.get(domain, 'channel'), media=post.photos)
        except Exception:
            log.warning('[TG] Невозможно отправить фото: {0}.'.format(sys.exc_info()[1]))
    for m in post.videos:
        try:
            bot.sendVideo(chat_id=config.get(domain, 'channel'), video=open(m, 'rb'), timeout=60)
        except Exception:
            pass
    for m in post.docs:
        bot.sendDocument(chat_id=config.get(domain, 'channel'), document=open(m, 'rb'), timeout=60)
    for (m, n) in post.tracks:
        try:
            if getsize(m) > 52428800:
                remove(m)
            else:
                try:
                    bot.sendAudio(chat_id=config.get(domain, 'channel'), audio=open(m, 'rb'), duration=int(n), timeout=60)
                except:
                    pass
                remove(m)
        except FileNotFoundError:
            continue
