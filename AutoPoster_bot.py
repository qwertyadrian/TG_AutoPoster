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


def get_data(URL):
    timeout = eventlet.Timeout(10)
    try:
        feed = requests.get(URL)
        return feed.json()
    except:
        logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()


def send_new_posts(items, last_id, group, CHAT_ID):
    for item in items:
        if item['id'] <= last_id:
            logging.info('New posts not detected. Switching to waiting...')
            break
        try:
            if item['attachments'][0]['type'] == 'photo' and len(item['attachments']) == 1:
                send_post_with_one_photo(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'photo' and len(item['attachments']) > 1:
                send_post_with_many_photos(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'link':
                send_post_with_link(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'doc':
                send_post_with_doc(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'video':
            	send_post_with_video(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'poll':
                # Функция отправки опросов не реализована
                send_post_with_poll(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'audio':
            	# Функция отправки аудиозаписей не реализована
            	send_post_with_music(item, group, CHAT_ID)
            else:
            	pass
        except KeyError:
            logging.warning('In the post, no text, photos, videos, links and documents not found.')
            if item['text'] != '':
                bot.sendMessage(CHAT_ID, item['text'])
            else:
                pass
    sleep(1)
    # Спим секунду, чтобы избежать разного рода ошибок и ограничений (на всякий случай!)
    return


def send_post_with_one_photo(post, group, CHAT_ID):
    try:
        photo = post['attachments'][0]['photo']['photo_75']
        photo = post['attachments'][0]['photo']['photo_130']
        photo = post['attachments'][0]['photo']['photo_604']
        photo = post['attachments'][0]['photo']['photo_807']
        photo = post['attachments'][0]['photo']['photo_1280']
        photo = post['attachments'][0]['photo']['photo_2560']
    except KeyError:
        pass
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + group
    caption_formatted = re.sub(pattern, '\n', caption)
    caption_formatted1 = re.sub(pattern1, '', caption_formatted)
    if len(caption_formatted) > 199:
        bot.sendPhoto(CHAT_ID, photo)
        bot.sendMessage(CHAT_ID, caption_formatted1)
    else:
        bot.sendPhoto(CHAT_ID, photo, caption_formatted1)
    sleep(5)


def send_post_with_many_photos(post, group, CHAT_ID):
    media = []
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + group
    caption_formatted = re.sub(pattern, '\n', caption)
    caption_formatted1 = re.sub(pattern1, '', caption_formatted)
    try:
        photo = post['attachments'][0]['photo']['photo_75']
        photo = post['attachments'][0]['photo']['photo_130']
        photo = post['attachments'][0]['photo']['photo_604']
        photo = post['attachments'][0]['photo']['photo_807']
        photo = post['attachments'][0]['photo']['photo_1280']
        photo = post['attachments'][0]['photo']['photo_2560']
    except KeyError:
        pass
    if len(caption_formatted) > 199:
        bot.sendPhoto(CHAT_ID, photo)
        bot.sendMessage(CHAT_ID, caption_formatted1)
    else:
        bot.sendPhoto(CHAT_ID, photo, caption_formatted1)
    for i in post['attachments'][1:]:
        if i['type'] == 'audio':
            # Функция отправки аудиозаписей не реализована
            pass
        elif i['type'] == 'poll':
            # Функция отправки опросов не реализована
            pass
        elif i['type'] == 'link':
            link = i['link']['url']
            title = i['link']['title']
            text = '[{0}]({1})'.format(title, text)
            bot.sendMessage(CHAT_ID, link, parse_mod='Markdown')
        else:
            try:
                photo = i['photo']['photo_75']
                photo = i['photo']['photo_130']
                photo = i['photo']['photo_604']
                photo = i['photo']['photo_807']
                photo = i['photo']['photo_1280']
                photo = i['photo']['photo_2560']
            except KeyError:
                pass
            media.append({'media': photo, 'type': 'photo'})
    if len(media) == 0:
        pass
    else:
        bot.sendMediaGroup(CHAT_ID, media)
    sleep(5)


def send_post_with_link(post, group, CHAT_ID):
    link = post['attachments'][0]['link']['url']
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + group
    caption_formatted = re.sub(pattern, '\n', caption)
    caption_formatted1 = re.sub(pattern1, '', caption_formatted) + '\n' + link
    bot.sendMessage(CHAT_ID, caption_formatted1)
    sleep(5)
    
    
def send_post_with_video(post, group, CHAT_ID):
    link = '{!s}{!s}{!s}{!s}'.format(BASE_VIDEO_URL, post['attachments'][0]['video']['owner_id'], '_', post['attachments'][0]['video']['id'])
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + group
    caption_formatted = re.sub(pattern, '\n', caption)
    caption_formatted1 = re.sub(pattern1, '', caption_formatted)
    text = caption_formatted1 + '\n' + link
    for i in post['attachments'][1:]:
        link = '{!s}{!s}{!s}{!s}'.format(BASE_VIDEO_URL, i['video']['owner_id'], '_', i['video']['id'])
        text = text + '\n' + link
    bot.sendMessage(CHAT_ID, text)
    sleep(5)

def send_post_with_doc(post, group, CHAT_ID):
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + group
    caption_formatted = re.sub(pattern, '\n', caption)
    caption_formatted1 = re.sub(pattern1, '', caption_formatted)
    document = post['attachments'][0]['doc']['url']
    if len(caption_formatted) > 199:
        bot.sendMessage(CHAT_ID, caption_formatted1)
        bot.sendPhoto(CHAT_ID, document)
    else:
        bot.sendDocument(CHAT_ID, document, caption_formatted1)
    for i in post['attachments'][1:]:
        bot.sendDocument(CHAT_ID, i['doc']['url'])
    sleep(5)
        
        
def send_post_with_poll(post, group, CHAT_ID):
	# Функция отправки опросов не реализована
    pass
    
    
def send_post_with_music(post, group, CHAT_ID):
    # Функция отправки аудиозаписей не реализована
    media = []
    caption = post['text']
    pattern = r'<br>'
    pattern1 = '@' + group
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
            try:
                photo = i['photo']['photo_75']
                photo = i['photo']['photo_130']
                photo = i['photo']['photo_604']
                photo = i['photo']['photo_807']
                photo = i['photo']['photo_1280']
                photo = i['photo']['photo_2560']
            except KeyError:
                pass
            media.append({'media': photo, 'type': 'photo'})
    bot.sendMediaGroup(CHAT_ID, media)
    sleep(5)


def check_new_posts_vk(URL, group, FILENAME_VK, CHAT_ID):
    # Пишем текущее время начала
    logging.info('[VK] Started scanning for new posts')
    with open(FILENAME_VK, 'rt') as file:
        last_id = int(file.read())
        if last_id is None:
            logging.error('Could not read from storage. Skipped iteration.')
            return
        logging.info('Last ID (VK) = {!s}'.format(last_id))
        feed = get_data(URL)
        # Если ранее случился таймаут, пропускаем итерацию. Если всё нормально - парсим посты.
        if feed is not None:
            entries = feed['response']['items']
            try:
                # Если пост был закреплен, пропускаем его
                tmp = entries[0]['is_pinned']
                # И запускаем отправку сообщений
                send_new_posts(entries[1:], last_id, group, CHAT_ID)
            except KeyError:
                send_new_posts(entries, last_id, group, CHAT_ID)
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
        for (key, value) in URLS.items():
            check_new_posts_vk(key, *value)
        logging.info('[App] Script went to sleep.')
        sleep(60 * 5)