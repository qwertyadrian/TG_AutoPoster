#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telepot import Bot
from eventlet import Timeout
from logging import basicConfig, warning, getLogger, error, INFO, CRITICAL, info
from vk_api import VkApi
from wget import download
from os import remove, listdir, mkdir, chdir, rename
from re import sub
from mutagen import id3, File
from urllib3 import exceptions
from mutagen.easyid3 import EasyID3
from vk_api.audio import VkAudio
from config import *
from time import sleep
from os.path import getsize
from fleep import get

bot = Bot(TOKEN)
session = VkApi(LOGIN, PASSWORD, auth_handler=auth_handler)
session.auth()
audio = VkAudio(session)
api = session.get_api()


def get_data(group):
    """
    Функция получения новых постов с серверов VK. В случае успеха возвращает словарь с постами, а в случае неудачи -
    ничего

    :param group: ID группы ВК
    :return: Возвращает словарь с постами
    """
    timeout = Timeout(10)
    # noinspection PyBroadException
    try:
        feed = api.wall.get(domain=group, count=11)
        return feed
    except Exception:
        warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()


def send_new_posts(items, last_id, group, CHAT_ID):
    """
    Функция отправки постов. Она распределяет посты различным категориям (отдельным функциям).

    :param items: Список постов
    :param last_id: ID последнего отправленного поста
    :param group: ID группы ВК
    :param CHAT_ID: ID чата, канала или ваш Telegram ID
    :return: None
    """
    for item in items:
        if item['id'] <= last_id:
            info('New posts not detected. Switching to waiting...')
            # Если новые посты не обнаружены пропускаем итерацию
            break
        try:
            if item['attachments'][0]['type'] == 'album':
                send_post_with_album(item, group, CHAT_ID)
            else:
                send_post(item, group, CHAT_ID)
        except KeyError:
            warning('In the post, no text, photos, videos, links and documents not found.')
            if item['text'] != '':
                bot.sendMessage(CHAT_ID, item['text'])
            else:
                pass
    sleep(1)
    # Спим секунду, чтобы избежать разного рода ошибок и ограничений (на всякий случай!)
    return


def send_post(post, group, CHAT_ID):
    photos = []
    tracks = []
    docs = []
    links = ''
    videos = []
    caption = post['text']
    pattern = '@' + group
    caption_formatted = sub(pattern, '', caption)
    for i in post['attachments']:
        if i['type'] == 'audio':
            track = i['audio']['artist'] + ' - ' + i['audio']['title']
            track_list = audio.search(q=track)
            for k in track_list:
                k_artist = sub(r"[^A-Za-zА-Яа-я()'-]", '', k['artist']).lower()
                k_title = sub(r"[^A-Za-zА-Яа-я()'-]", '', k['title']).lower()
                i_artist = sub(r"[^A-Za-zА-Яа-я()'-]", '', i['audio']['artist']).lower()
                i_title = sub(r"[^A-Za-zА-Яа-я()'-]", '', i['audio']['title']).lower()
                if k_artist == i_artist and k_title == i_title:
                    name = sub(r"[/\"?:|<>*]", '', k['artist'] + ' - ' + k['title'] + '.mp3')
                    file = download(k['url'], out=name)
                    try:
                        music = EasyID3(file)
                    except id3.ID3NoHeaderError:
                        music = File(file, easy=True)
                        music.add_tags()
                    music['title'] = i['audio']['title']
                    music['artist'] = i['audio']['artist']
                    music.save()
                    del music
                    tracks.append(name)
                    break
        elif i['type'] == 'link':
            link = i['link']['url']
            title = i['link']['title']
            text = '[{0}]({1})'.format(title, link)
            links += text + '\n'
            # bot.sendMessage(CHAT_ID, text, parse_mode='Markdown')
        elif i['type'] == 'doc':
            doc = download(i['doc']['url'], out='file')
            with open(doc, 'rb') as file:
                mime = get(file.read(128))
            new_doc = doc + '.' + mime.extension[0]
            rename(doc, new_doc)
            if getsize(new_doc) < 52428800:
                # bot.sendDocument(CHAT_ID, open(new_doc, 'rb'))
                # remove(new_doc)
                docs.append(open(new_doc, 'rb'))
            else:
                remove(new_doc)
        elif i['type'] == 'photo':
            photo = i['photo']['photo_75']
            try:
                photo = i['photo']['photo_130']
                photo = i['photo']['photo_604']
                photo = i['photo']['photo_807']
                photo = i['photo']['photo_1280']
                photo = i['photo']['photo_2560']
            except KeyError:
                pass
            photos.append({'media': open(download(photo), 'rb'), 'type': 'photo'})
        elif i['type'] == 'video':
            link = '{!s}{!s}{!s}{!s}'.format(BASE_VIDEO_URL, i['video']['owner_id'], '_', i['video']['id'])
            videos.append(link)
            # text = text + '\n' + link
            # bot.sendMessage(CHAT_ID, text)
        else:
            # Если тип вложения не определен, он не будет обработан
            # Поддержка других  вложений будет реализована в будущем
            pass
    if photos and caption_formatted:
        if len(photos) == 1:
            if len(caption_formatted) < 200:
                bot.sendPhoto(CHAT_ID, photos.pop(0)['media'], caption_formatted)
            else:
                bot.sendMessage(CHAT_ID, caption_formatted)
                bot.sendPhoto(CHAT_ID, photos.pop(0)['media'])
        else:
            if len(caption_formatted) < 200:
                bot.sendPhoto(CHAT_ID, photos.pop(0)['media'], caption_formatted)
                bot.sendMediaGroup(CHAT_ID, photos)
            else:
                bot.sendMessage(CHAT_ID, caption_formatted)
                bot.sendMediaGroup(CHAT_ID, photos)
    elif caption_formatted:
        bot.sendMessage(CHAT_ID, caption_formatted)
    elif photos:
        info('Text in post not found. Skipping sending text message')
        bot.sendMediaGroup(CHAT_ID, photos)
    if links:
        bot.sendMessage(CHAT_ID, links)
    for m in videos:
        bot.sendMessage(CHAT_ID, m)
    for m in docs:
        bot.sendDocument(CHAT_ID, m)
    for m in tracks:
        try:
            if getsize(m) > 52428800:
                remove(m)
            else:
                bot.sendAudio(CHAT_ID, open(m, 'rb'))
            remove(m)
        except FileNotFoundError:
            continue
        

def send_post_with_album(post, group, CHAT_ID):
    """
    Функция отправки альбома.

    :param post: Пост, в котором есть прикрепленный альбом.
    :param group: ID группы ВК
    :param CHAT_ID: ID чата, канала или ваш Telegram ID
    :return: None
    """
    media = []
    caption = post['text']
    pattern = '@' + group
    caption_formatted = sub(pattern, '', caption)
    bot.sendMessage(CHAT_ID, caption_formatted)
    album = api.photos.get(owner_id=post['attachments'][0]['album']['owner_id'],
                           album_id=int(post['attachments'][0]['album']['id']), count=1000)['items']
    for i in album:
        photo = i['photo_75']
        try:
            photo = i['photo_130']
            photo = i['photo_604']
            photo = i['photo_807']
            photo = i['photo_1280']
            # photo = i['photo_2560']
        except KeyError:
            pass
        if len(media) == 10:
            timeout = Timeout(45)
            try:
                bot.sendMediaGroup(CHAT_ID, media)
            except exceptions.ReadTimeoutError:
                print('Попытка отправки альбома не удалась. Повтор...')
                sleep(5)
                bot.sendMediaGroup(CHAT_ID, media)
            finally:
                timeout.cancel()
            media = []
        else:
            media.append({'media': photo, 'type': 'photo'})
    return


def check_new_posts_vk(group, FILENAME_VK, CHAT_ID):
    """
    Основная функция программы. В ней вызываются остальные функции.
    Посты передаются в функцию send_new_posts

    :param group: Короткое название группы
    :param FILENAME_VK: Имя файла, в котором сохраняется ID почледнего отправленного поста.
    :param CHAT_ID: ID чата, в который отправляются посты
    :return: None
    """
    # Пишем текущее время начала
    info('[VK] Started scanning for new posts')
    try:
        with open(FILENAME_VK, 'rt'):
            pass
    except FileNotFoundError:
        f = open(FILENAME_VK, 'w')
        f.write('0')
        f.close()
    with open(FILENAME_VK, 'rt') as file:
        last_id = int(file.read())
        if last_id is None:
            error('Could not read from storage. Skipped iteration.')
            return
        info('Last ID (VK) = {!s}'.format(last_id))
        feed = get_data(group)
        # Если ранее случился таймаут, пропускаем итерацию. Если всё нормально - парсим посты.
        if feed is not None:
            entries = feed['items']
            try:
                # Если пост был закреплен, пропускаем его
                assert entries[0]['is_pinned']
                # И запускаем отправку сообщений
                send_new_posts(entries[1:], last_id, group, CHAT_ID)
            except KeyError:
                send_new_posts(entries, last_id, group, CHAT_ID)
            # Записываем новый last_id в файл.
            # noinspection PyAssignmentToLoopOrWithParameter
            with open(FILENAME_VK, 'wt') as file:
                try:
                    assert entries[0]['is_pinned']
                    # Если первый пост - закрепленный, то сохраняем ID второго
                    file.write(str(entries[1]['id']))
                    info('New last_id (VK) is {!s}'.format((entries[1]['id'])))
                except KeyError:
                    file.write(str(entries[0]['id']))
                    info('New last_id (VK) is {!s}'.format((entries[0]['id'])))
    info('[VK] Finished scanning')
    return


if __name__ == '__main__':
    getLogger('AutoPoster').setLevel(CRITICAL)
    basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', level=INFO,
                filename='bot_log.log', datefmt='%d.%m.%Y %H:%M:%S')
    try:
        mkdir('data')
        chdir('data')
    except FileExistsError:
        chdir('data')
    if SINGLE_RUN:
        for (key, value) in URLS.items():
            check_new_posts_vk(key, *value)
        for data in listdir('.'):
            remove(data)
        info('[App] Script exited.\n')
    else:
        while True:
            for (key, value) in URLS.items():
                check_new_posts_vk(key, *value)
            for data in listdir('.'):
                remove(data)
            info('[App] Script went to sleep.')
            sleep(60 * 5)
