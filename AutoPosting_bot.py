#!/usr/bin/env python
# -*- coding: utf-8 -*-
import telepot
import requests
import eventlet
import logging
import re
from config import *
from time import sleep

bot = telepot.Bot(TOKEN)


def get_data():
    timeout = eventlet.Timeout(10)
    try:
        feed = requests.get(URL_VK)
        return feed.json()
    except:
        logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()


def send_new_posts(items, last_id):
    for item in items:
        if item['id'] <= last_id:
            logging.info('New posts not detected. Switching to waiting...')
            break
        if item['attachment']['type'] == 'photo' and len(item['attachments']) == 1:
            send_post_with_one_photo(item)
        elif item['attachment']['type'] == 'photo' and len(item['attachments']) > 1:
            send_post_with_many_photos(item)
        elif item['attachment']['type'] == 'link':
            send_post_with_link(item)
        elif item['attachment']['type'] == 'doc':
            send_post_with_doc(item)
        elif item['attachment']['type'] == 'video':
        	send_post_with_video(item)
        elif item['attachment']['type'] == 'poll':
            # Функция отправки опросов не реализована
            send_post_with_poll(item)
        elif item['attachment']['type'] == 'audio':
        	# Функция отправки аудиозаписей не реализована
        	send_post_with_music(item)
        else:
        	logging.warning('In the post, no text, photos, videos, links and documents not found.')
    # Спим секунду, чтобы избежать разного рода ошибок и ограничений (на всякий случай!)
    sleep(1)
    return


def send_post_with_one_photo(post):
    photo = post['attachment']['photo']['src_big']
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + GROUP
    caption_formatted = re.sub(pattern, '\n', caption)
    caption_formatted1 = re.sub(pattern1, '', caption_formatted)
    if len(caption_formatted) > 199:
        bot.sendPhoto(CHAT_ID, photo)
        bot.sendMessage(CHAT_ID, caption_formatted1)
    else:
        bot.sendPhoto(CHAT_ID, photo, caption_formatted1)
    sleep(5)


def send_post_with_many_photos(post):
    media = []
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + GROUP
    caption_formatted = re.sub(pattern, '\n', caption)
    caption_formatted1 = re.sub(pattern1, '', caption_formatted)
    photo = post['attachment']['photo']['src_big']
    if len(caption_formatted) > 199:
        bot.sendPhoto(CHAT_ID, photo)
        bot.sendMessage(CHAT_ID, caption_formatted1)
    else:
        bot.sendPhoto(CHAT_ID, photo, caption_formatted1)
    for i in post['attachments'][1:]:
        if i['type'] == 'audio':
            # Функция отправки аудиозаписей не реализована
            pass
        else:
            photo = i['photo']['src_big']
            media.append({'media': photo, 'type': 'photo'})
    if len(media) == 0:
        pass
    else:
        bot.sendMediaGroup(CHAT_ID, media)
    sleep(5)


def send_post_with_link(post):
    link = post['attachment']['link']['url']
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + GROUP
    caption_formatted = re.sub(pattern, '\n', caption)
    caption_formatted1 = re.sub(pattern1, '', caption_formatted) + '\n' + link
    bot.sendMessage(CHAT_ID, caption_formatted1)
    sleep(5)
    
    
def send_post_with_video(post):
    link = '{!s}{!s}{!s}{!s}'.format(BASE_VIDEO_URL, post['attachment']['video']['owner_id'], '_', post['attachment']['video']['vid'])
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + GROUP
    caption_formatted = re.sub(pattern, '\n', caption)
    caption_formatted1 = re.sub(pattern1, '', caption_formatted)
    text = caption_formatted1 + '\n' + link
    bot.sendMessage(CHAT_ID, text)
    sleep(5)

def send_post_with_doc(post):
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + GROUP
    caption_formatted = re.sub(pattern, '\n', caption)
    caption_formatted1 = re.sub(pattern1, '', caption_formatted)
    document = post['attachment']['doc']['url']
    if len(caption_formatted) > 199:
        bot.sendMessage(CHAT_ID, caption_formatted1)
        bot.sendPhoto(CHAT_ID, document)
    else:
        bot.sendDocument(CHAT_ID, document, caption_formatted1)
    for i in post['attachments'][1:]:
        bot.sendDocument(CHAT_ID, i['doc']['url'])
    sleep(5)
        
        
def send_post_with_poll(post):
	# Функция отправки опросов не реализована
    pass
    
    
def send_post_with_music(post):
    # Функция отправки аудиозаписей не реализована
    media = []
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + GROUP
    caption_formatted = re.sub(pattern, '\n', caption)
    caption_formatted1 = re.sub(pattern1, '', caption_formatted)
    if caption == '':
        caption_formatted = None
    else:
        bot.sendMessage(CHAT_ID, caption_formatted1)
    for i in post['attachments'][1:]:
        if i['type'] == 'audio':
            # Функция отправки аудиозаписей не реализована
            pass
        elif i['type'] == 'doc':
            bot.sendDocument(CHAT_ID, i['doc']['url'])
        else:
            photo = i['photo']['src_big']
            media.append({'media': photo, 'type': 'photo'})
    bot.sendMediaGroup(CHAT_ID, media)
    sleep(5)


def check_new_posts_vk():
    # Пишем текущее время начала
    logging.info('[VK] Started scanning for new posts')
    with open(FILENAME_VK, 'rt') as file:
        last_id = int(file.read())
        if last_id is None:
            logging.error('Could not read from storage. Skipped iteration.')
            return
        logging.info('Last ID (VK) = {!s}'.format(last_id))
        feed = get_data()
        # Если ранее случился таймаут, пропускаем итерацию. Если всё нормально - парсим посты.
        if feed is not None:
            entries = feed['response'][1:]
            try:
                # Если пост был закреплен, пропускаем его
                tmp = entries[0]['is_pinned']
                # И запускаем отправку сообщений
                send_new_posts(entries[1:], last_id)
            except KeyError:
                send_new_posts(entries, last_id)
            # Записываем новый last_id в файл.
            with open(FILENAME_VK, 'wt') as file:
                try:
                    tmp = entries[0]['is_pinned']
                    # Если первый пост - закрепленный, то сохраняем ID второго
                    file.write(str(entries[1]['id']))
                    logging.info('New last_id (VK) is {!s}'.format((entries[1]['id'])))
                except KeyError:
                    file.write(str(entries[0]['id']))
                    logging.info('New last_id (VK) is {!s}'.format((entries[0]['id'])))
    logging.info('[VK] Finished scanning')
    return


if __name__ == '__main__':
    while True:
        logging.getLogger('requests').setLevel(logging.CRITICAL)
        logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s',
                            level=logging.INFO, filename='bot_log.log', datefmt='%d.%m.%Y %H:%M:%S')
        check_new_posts_vk()
        logging.info('[App] Script went to sleep.')
        sleep(60 * 5)
