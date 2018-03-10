#!/usr/bin/env python
# -*- coding: utf-8 -*-
from telepot import Bot
from eventlet import Timeout
from logging import basicConfig, warning, getLogger, error, INFO, CRITICAL, info
from vk_api import VkApi
from wget import download
from os import rename, remove
from re import sub
from mutagen import id3, File
from urllib3 import exceptions
from mutagen.easyid3 import EasyID3
from vk_api.audio import VkAudio
from config import *
from time import sleep
from os.path import getsize

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
    :param CHAT_ID: ID чата/канала Telegram
    :return: None
    """
    for item in items:
        if item['id'] <= last_id:
            info('New posts not detected. Switching to waiting...')
            # Если новые посты не обнаружены пропускаем итерацию
            break
        try:
            if item['attachments'][0]['type'] == 'photo' and len(item['attachments']) == 1:
                # Если первый первый прикрепленный файл - фото и оно одно, то выполняется фунция ниже
                send_post_with_one_photo(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'photo' and len(item['attachments']) > 1:
                # Если первый первый прикрепленный файл - фото их несколько, то выполняется фунция ниже
                send_post_with_many_photos(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'link':
                # Если первый первый прикрепленный файл - ссылка, то выполняется фунция ниже
                send_post_with_link(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'doc':
                # Если первый первый прикрепленный файл - документ, то выполняется фунция ниже
                send_post_with_doc(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'video':
                # Если первый первый прикрепленный файл - видео, то выполняется фунция ниже
                send_post_with_video(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'poll':
                # Функция отправки опросов не реализована
                pass
            elif item['attachments'][0]['type'] == 'audio':
                # Функция отправки аудиозаписей не реализована
                send_post_with_music(item, group, CHAT_ID)
            elif item['attachments'][0]['type'] == 'album':
                send_post_with_album(item, group, CHAT_ID)
            else:
                pass
        except KeyError:
            warning('In the post, no text, photos, videos, links and documents not found.')
            if item['text'] != '':
                bot.sendMessage(CHAT_ID, item['text'])
            else:
                pass
    sleep(1)
    # Спим секунду, чтобы избежать разного рода ошибок и ограничений (на всякий случай!)
    return


def send_post_with_one_photo(post, group, CHAT_ID):
    """
    Функция отправки поста с одним фото.
    :param post: Словарь с информацией о посте
    :param group: ID группы ВК
    :param CHAT_ID: ID чата/канала Telegram
    :return: None
    """
    try:
        photo = post['attachments'][0]['photo']['photo_75']
        photo = post['attachments'][0]['photo']['photo_130']
        photo = post['attachments'][0]['photo']['photo_604']
        photo = post['attachments'][0]['photo']['photo_807']
        photo = post['attachments'][0]['photo']['photo_1280']
        # photo = post['attachments'][0]['photo']['photo_2560']
    except KeyError:
        pass
    caption = post['text']
    pattern = '@' + group
    caption_formatted = sub(pattern, '', caption)
    if len(caption_formatted) > 199:
        bot.sendPhoto(CHAT_ID, photo)
        bot.sendMessage(CHAT_ID, caption_formatted)
    else:
        bot.sendPhoto(CHAT_ID, photo, caption_formatted)
    sleep(5)


def send_post_with_many_photos(post, group, CHAT_ID):
    """
    Функция отправки поста с несколькими фото (вложениями)
    :param post: Словарь с информацией о посте
    :param group: ID группы ВК
    :param CHAT_ID: ID чата/канала Telegram
    :return: None
    """
    media = []
    tracks = []
    caption = post['text']
    pattern = '@' + group
    caption_formatted = sub(pattern, '', caption)
    try:
        photo = post['attachments'][0]['photo']['photo_75']
        photo = post['attachments'][0]['photo']['photo_130']
        photo = post['attachments'][0]['photo']['photo_604']
        photo = post['attachments'][0]['photo']['photo_807']
        photo = post['attachments'][0]['photo']['photo_1280']
        # photo = post['attachments'][0]['photo']['photo_2560']
    except KeyError:
        pass
    if len(caption_formatted) > 199:
        bot.sendPhoto(CHAT_ID, photo)
        bot.sendMessage(CHAT_ID, caption_formatted)
    else:
        bot.sendPhoto(CHAT_ID, photo, caption_formatted)
    for i in post['attachments'][1:]:
        if i['type'] == 'audio':
            track = i['audio']['artist'] + ' - ' + i['audio']['title']
            track_list = audio.search(q=track)
            for k in track_list:
                k_artist = sub(r"[^A-Za-zА-Яа-я()'-]", '', k['artist']).lower()
                k_title = sub(r"[^A-Za-zА-Яа-я()'-]", '', k['title']).lower()
                i_artist = sub(r"[^A-Za-zА-Яа-я()'-]", '', i['audio']['artist']).lower()
                i_title = sub(r"[^A-Za-zА-Яа-я()'-]", '', i['audio']['title']).lower()
                if k_artist == i_artist and k_title == i_title:
                    file = download(k['url'])
                    name = sub(r"[/\"?:|<>*]", '', k['artist'] + ' - ' + k['title'] + '.mp3')
                    rename(file, name)
                    try:
                        music = EasyID3(name)
                    except id3.ID3NoHeaderError:
                        music = File(name, easy=True)
                        music.add_tags()
                    music['title'] = i['audio']['title']
                    music['artist'] = i['audio']['artist']
                    music.save()
                    del music
                    tracks.append(name)
                    break
        elif i['type'] == 'poll':
            # Функция отправки опросов не реализована
            pass
        elif i['type'] == 'link':
            link = i['link']['url']
            title = i['link']['title']
            text = '[{0}]({1})'.format(title, link)
            bot.sendMessage(CHAT_ID, text, parse_mode='Markdown')
        elif i['type'] == 'doc':
            file = download(i['doc']['url'])
            rename(file, i['doc']['title'])
            if getsize(i['doc']['title']) < 52428800:
                bot.sendDocument(CHAT_ID, i['doc']['url'])
                remove(i['doc']['title'])
        else:
            try:
                photo = i['photo']['photo_75']
                photo = i['photo']['photo_130']
                photo = i['photo']['photo_604']
                photo = i['photo']['photo_807']
                photo = i['photo']['photo_1280']
                # photo = i['photo']['photo_2560']
            except KeyError:
                pass
            media.append({'media': photo, 'type': 'photo'})
    if len(media) == 0:
        pass
    else:
        bot.sendMediaGroup(CHAT_ID, media)
    for m in tracks:
        bot.sendAudio(CHAT_ID, open(m, 'rb'))
        remove(m)
    sleep(5)


def send_post_with_link(post, group, CHAT_ID):
    """
    Функция отправки поста с ссылкой.
    :param post: Словарь с информацией о посте
    :param group: ID группы ВК
    :param CHAT_ID: ID чата/канала Telegram
    :return: None
    """
    link = post['attachments'][0]['link']['url']
    caption = post['text']
    pattern = '@' + group
    caption_formatted = sub(pattern, '', caption) + '\n' + link
    bot.sendMessage(CHAT_ID, caption_formatted)
    sleep(5)


def send_post_with_album(post, group, CHAT_ID):
    media = []
    caption = post['text']
    pattern = '@' + group
    caption_formatted = sub(pattern, '', caption)
    bot.sendMessage(CHAT_ID, caption_formatted)
    album = api.photos.get(owner_id=post['attachments'][0]['album']['owner_id'],
                           album_id=int(post['attachments'][0]['album']['id']), count=1000)['items']
    for i in album:
        try:
            photo = i['photo_75']
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


def send_post_with_video(post, group, CHAT_ID):
    """
    Функция отправки поста с видео.
    :param post: Словарь с информацией о посте
    :param group: ID группы ВК
    :param CHAT_ID: ID чата/канала Telegram
    :return: None
    """
    link = '{!s}{!s}{!s}{!s}'.format(BASE_VIDEO_URL, post['attachments'][0]['video']['owner_id'], '_',
                                     post['attachments'][0]['video']['id'])
    caption = post['text']
    pattern = '@' + group
    caption_formatted = sub(pattern, '', caption)
    text = caption_formatted + '\n' + link
    for i in post['attachments'][1:]:
        link = '{!s}{!s}{!s}{!s}'.format(BASE_VIDEO_URL, i['video']['owner_id'], '_', i['video']['id'])
        text = text + '\n' + link
    bot.sendMessage(CHAT_ID, text)
    sleep(5)


def send_post_with_doc(post, group, CHAT_ID):
    """
    Функция отправки поста с документом.
    :param post: Словарь с информацией о посте
    :param group: ID группы ВК
    :param CHAT_ID: ID чата/канала Telegram
    :return: None
    """
    caption = post['text']
    pattern = '@' + group
    caption_formatted = sub(pattern, '', caption)
    document = post['attachments'][0]['doc']['url']
    tracks = []
    media = []
    if len(caption_formatted) > 199:
        bot.sendMessage(CHAT_ID, caption_formatted)
        bot.sendPhoto(CHAT_ID, document)
    else:
        bot.sendDocument(CHAT_ID, document, caption_formatted)
    for i in post['attachments'][1:]:
        if i['type'] == 'audio':
            track = i['audio']['artist'] + ' - ' + i['audio']['title']
            track_list = audio.search(q=track)
            for k in track_list:
                k_artist = sub(r"[^A-Za-zА-Яа-я()'-]", '', k['artist']).lower()
                k_title = sub(r"[^A-Za-zА-Яа-я()'-]", '', k['title']).lower()
                i_artist = sub(r"[^A-Za-zА-Яа-я()'-]", '', i['audio']['artist']).lower()
                i_title = sub(r"[^A-Za-zА-Яа-я()'-]", '', i['audio']['title']).lower()
                if k_artist == i_artist and k_title == i_title:
                    file = download(k['url'])
                    name = sub(r"[/\"?:|<>*]", '', k['artist'] + ' - ' + k['title'] + '.mp3')
                    rename(file, name)
                    try:
                        music = EasyID3(name)
                    except id3.ID3NoHeaderError:
                        music = File(name, easy=True)
                        music.add_tags()
                    music['title'] = i['audio']['title']
                    music['artist'] = i['audio']['artist']
                    music.save()
                    del music
                    tracks.append(name)
                    break
        elif i['type'] == 'doc':
            file = download(i['doc']['url'])
            rename(file, i['doc']['title'])
            if getsize(i['doc']['title']) < 52428800:
                bot.sendDocument(CHAT_ID, i['doc']['url'])
                remove(i['doc']['title'])
            else:
                remove(i['doc']['title'])
        elif i['type'] == 'poll':
            pass
        elif i['type'] == 'link':
            link = i['link']['url']
            title = i['link']['title']
            text = '[{0}]({1})'.format(title, link)
            bot.sendMessage(CHAT_ID, text, parse_mode='Markdown')
        else:
            try:
                photo = i['photo']['photo_75']
                photo = i['photo']['photo_130']
                photo = i['photo']['photo_604']
                photo = i['photo']['photo_807']
                photo = i['photo']['photo_1280']
                # photo = i['photo']['photo_2560']
            except KeyError:
                pass
            media.append({'media': photo, 'type': 'photo'})
    if len(media) == 0:
        pass
    else:
        bot.sendMediaGroup(CHAT_ID, media)
    for m in tracks:
        bot.sendAudio(CHAT_ID, open(m, 'rb'))
        remove(m)
    sleep(5)


def send_post_with_music(post, group, CHAT_ID):
    """
    Функция отправки постов с музыкой (не реализовано до конца)
    :param post: Словарь с информацией о посте
    :param group: ID группы ВК
    :param CHAT_ID: ID чата/канала Telegram
    :return: None
    """
    media = []
    tracks = []
    caption = post['text']
    pattern = '@' + group
    caption_formatted = sub(pattern, '', caption)
    if caption == '':
        pass
    else:
        bot.sendMessage(CHAT_ID, caption_formatted)
    for i in post['attachments'][1:]:
        if i['type'] == 'audio':
            track = i['audio']['artist'] + ' - ' + i['audio']['title']
            track_list = audio.search(q=track)
            for k in track_list:
                k_artist = sub(r"[^A-Za-zА-Яа-я()'-]", '', k['artist']).lower()
                k_title = sub(r"[^A-Za-zА-Яа-я()'-]", '', k['title']).lower()
                i_artist = sub(r"[^A-Za-zА-Яа-я()'-]", '', i['audio']['artist']).lower()
                i_title = sub(r"[^A-Za-zА-Яа-я()'-]", '', i['audio']['title']).lower()
                if k_artist == i_artist and k_title == i_title:
                    file = download(k['url'])
                    name = sub(r"[/\"?:|<>*]", '', k['artist'] + ' - ' + k['title'] + '.mp3')
                    rename(file, name)
                    try:
                        music = EasyID3(name)
                    except id3.ID3NoHeaderError:
                        music = File(name, easy=True)
                        music.add_tags()
                    music['title'] = i['audio']['title']
                    music['artist'] = i['audio']['artist']
                    music.save()
                    del music
                    tracks.append(name)
                    break
        elif i['type'] == 'doc':
            file = download(i['doc']['url'])
            rename(file, i['doc']['title'])
            if getsize(i['doc']['title']) < 52428800:
                bot.sendDocument(CHAT_ID, i['doc']['url'])
                remove(i['doc']['title'])
        else:
            try:
                photo = i['photo']['photo_75']
                photo = i['photo']['photo_130']
                photo = i['photo']['photo_604']
                photo = i['photo']['photo_807']
                photo = i['photo']['photo_1280']
                # photo = i['photo']['photo_2560']
            except KeyError:
                pass
            media.append({'media': photo, 'type': 'photo'})
    try:
        bot.sendMediaGroup(CHAT_ID, media)
    except ValueError:
        pass
    for m in tracks:
        bot.sendAudio(CHAT_ID, open(m, 'rb'))
        remove(m)
    sleep(5)


def check_new_posts_vk(group, FILENAME_VK, CHAT_ID):
    """
    Основная функция программы. В ней вызываются остальные функции.
    Посты передаются в функцию send_new_posts
    :param group: Короткое название группы
    :param FILENAME_VK: Название файла, в котором сохраняется ID  почледнего отправленного поста.
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
                tmp = entries[0]['is_pinned']
                # И запускаем отправку сообщений
                send_new_posts(entries[1:], last_id, group, CHAT_ID)
            except KeyError:
                send_new_posts(entries, last_id, group, CHAT_ID)
            # Записываем новый last_id в файл.
            # noinspection PyAssignmentToLoopOrWithParameter
            with open(FILENAME_VK, 'wt') as file:
                try:
                    tmp = entries[0]['is_pinned']
                    # Если первый пост - закрепленный, то сохраняем ID второго
                    file.write(str(entries[1]['id']))
                    info('New last_id (VK) is {!s}'.format((entries[1]['id'])))
                except KeyError:
                    file.write(str(entries[0]['id']))
                    info('New last_id (VK) is {!s}'.format((entries[0]['id'])))
    info('[VK] Finished scanning')
    return


if __name__ == '__main__':
    while True:
        getLogger('requests').setLevel(CRITICAL)
        basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', level=INFO,
                    filename='bot_log.log', datefmt='%d.%m.%Y %H:%M:%S')
        for (key, value) in URLS.items():
            check_new_posts_vk(key, *value)
        info('[App] Script went to sleep.')
        sleep(60 * 5)
