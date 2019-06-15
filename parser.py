import urllib
import sys
from os.path import getsize
import time
import configparser
from wget import download
from re import sub, compile, finditer, MULTILINE
from mutagen.easyid3 import EasyID3
from mutagen import id3, File
from telegram import InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from bs4 import BeautifulSoup
from vk_api.audio_url_decoder import decode_audio_url
from vk_api import exceptions
from tools import update_parameter
from logger import logger as log


def get_data(group, api_vk):
    """
    Функция получения новых постов с серверов VK. В случае успеха возвращает словарь с постами, а в случае неудачи -
    ничего

    :param api_vk: Экземпляр класса VkApiMethod
    :param group: ID группы ВК
    :return: Возвращает словарь с постами
    """
    # noinspection PyBroadException
    try:
        feed = api_vk.wall.get(domain=group, count=11)
        return feed['items']
    except Exception:
        log.exception('Ошибка получения информации о новых постах: {0}'.format(sys.exc_info()[0]))
        return None


def get_posts(domain, last_id, api_vk, config, session):
    log.info('[VK] Проверка на наличие новых постов в {0} с последним ID {1}'.format(domain, last_id))
    posts = get_data(domain, api_vk)
    for post in reversed(posts):
        if post['id'] > last_id:
            log.info("[VK] Обнаружен новый пост с ID {0}".format(post['id']))
            new_post = VkPostParser(post, domain, session, api_vk, config)
            new_post.generate_post()
            if 'copy_history' in new_post.post and not config.getboolean('global', 'send_reposts'):
                continue
            else:
                yield new_post
            if new_post.repost:
                yield new_post.repost
            update_parameter(config, domain, 'last_id', post['id'])
            last_id = post['id']
            time.sleep(5)
        elif post['id'] == last_id:
            log.info('[VK] Новых постов больше не обнаружено')
        else:
            if post.get('is_pinned', False):
                continue


class VkPostParser:
    def __init__(self, post, group, session, api_vk, config, its_repost=False, what_to_parse=None):
        self.youtube_link = 'https://youtube.com/watch?v='
        self.regex = compile(r'/(\S*?)\?')
        self.remixmdevice = '1920/1080/1/!!-!!!!'
        self.session = session
        self.api_vk = api_vk
        self.config = config
        self.pattern = '@' + group
        self.group = group
        self.post = post
        self.text = ''
        self.user = None
        self.links = None
        self.repost = None
        self.repost_source = None
        self.reply_markup = None
        self.photos = []
        self.videos = []
        self.docs = []
        self.tracks = []
        self.attachments_types = []
        self.its_repost = its_repost
        self.what_to_parse = what_to_parse

    def generate_post(self):
        log.info('[AP] Парсинг поста...')
        if not self.its_repost:
            try:
                self.what_to_parse = self.config.get(self.group, 'what_to_send').split(',')
            except configparser.NoOptionError:
                self.what_to_parse = self.config.get('global', 'what_to_send').split(',')
        if self.config.getboolean('global', 'sign_posts'):
            self.generate_user()
        if 'attachments' in self.post:
            for attachment in self.post['attachments']:
                self.attachments_types.append(attachment['type'])
        if set(self.what_to_parse).intersection({'text', 'all'}):
            self.generate_text()
        if set(self.what_to_parse).intersection({'photo', 'all'}):
            self.generate_photos()
        if set(self.what_to_parse).intersection({'video', 'all'}):
            self.generate_videos()
        if set(self.what_to_parse).intersection({'doc', 'all'}):
            self.generate_docs()
        if set(self.what_to_parse).intersection({'music', 'all'}):
            self.generate_music()
        self.generate_repost()

    def generate_text(self):
        if self.post['text']:
            log.info('[AP] Обнаружен текст. Извлечение...')
            self.text += self.post['text']
            self.text = self.text.replace(self.pattern, '')
            post = 'https://vk.com/wall%(owner_id)s_%(id)s' % self.post
            self.generate_links()
            if self.config.getboolean('global', 'sign_posts') and self.user:
                log.info('[AP] Подписывание поста и добавление ссылки на его оригинал.')
                user = 'https://vk.com/%(domain)s' % self.user
                button_list = [InlineKeyboardButton('Автор поста: %(first_name)s %(last_name)s' % self.user, url=user),
                               InlineKeyboardButton('Оригинал поста', url=post)]
                self.reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
            elif self.config.getboolean('global', 'sign_posts') and not self.user:
                log.info('[AP] Добавление только ссылки на оригинал поста, так как в нем не указан автор.')
                button_list = [InlineKeyboardButton('Оригинал поста', url=post)]
                self.reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
            matches = finditer(r'\[(.*?)\]', self.text, MULTILINE)
            result = {}
            for matchNum, match in enumerate(matches):
                for group_num in range(0, len(match.groups())):
                    group_num = group_num + 1
                    result[match.group()] = match.group(group_num)
            try:
                for i in result.keys():
                    self.text = self.text.replace(i, '<a href="https://vk.com/{}">{}</a>'.format(*result[i].split('|')))
            except IndexError:
                pass

    def generate_links(self):
        if 'attachments' in self.post:
            for attachment in self.post['attachments']:
                if attachment['type'] == 'link':
                    self.text += '\n🔗 <a href="%(url)s">%(title)s</a>' % attachment['link']
                elif attachment['type'] == 'page':
                    self.text += '\n🔗 <a href="%(view_url)s">%(title)s</a>' % attachment['page']
                elif attachment['type'] == 'album':
                    self.text += '\n<a href="https://vk.com/wall%(owner_id)s_%(id)s">' \
                                 'Фото альбом: %(title)s</a>' % attachment['album']

    def generate_photos(self):
        if 'photo' in self.attachments_types:
            log.info('[AP] Извлечение фото...')
            for attachment in self.post['attachments']:
                if attachment['type'] == 'photo':
                    photo = attachment['photo']['photo_75']
                    try:
                        photo = attachment['photo']['photo_130']
                        photo = attachment['photo']['photo_604']
                        photo = attachment['photo']['photo_807']
                        photo = attachment['photo']['photo_1280']
                        photo = attachment['photo']['photo_2560']
                    except KeyError:
                        pass
                    # self.photos.append({'media': open(download(photo), 'rb'), 'type': 'photo'})
                    self.photos.append(InputMediaPhoto(photo))

    def generate_docs(self):
        if 'doc' in self.attachments_types:
            log.info('[AP] Извлечение вложениий (файлы, гифки и т.п.)...')
            for attachment in self.post['attachments']:
                if attachment['type'] == 'doc' and attachment['doc']['size'] < 52428800:
                    try:
                        doc = download(attachment['doc']['url'],
                                       out=attachment['doc']['title'] + '.' + attachment['doc']['ext'])
                        self.docs.append(doc)
                    except urllib.error.URLError:
                        log.exception('[AP] Невозможно скачать вложенный файл: {0}.'.format(sys.exc_info()[1]))
                        self.text += '\n📃 <a href="%(url)s">%(title)s</a>' % attachment['doc']
                elif attachment['type'] == 'doc' and attachment['doc']['size'] >= 52428800:
                    self.text += '\n📃 <a href="%(url)s">%(title)s</a>' % attachment['doc']

    def generate_videos(self):
        if 'video' in self.attachments_types:
            log.info('[AP] Извлечение видео...')
            log.info('[AP] Данная функция находится в стадии тестирования. '
                     'В некоторых видео может быть только звук, а может вообще не запуститься.')
            for attachment in self.post['attachments']:
                if attachment['type'] == 'video':
                    video = 'https://m.vk.com/video%(owner_id)s_%(id)s' % attachment['video']
                    soup = BeautifulSoup(self.session.http.get(video).text, 'html.parser')
                    if soup.find_all('source'):
                        video_link = soup.find_all('source')[1].get('src')
                        file = download(video_link)
                        if getsize(file) > 52428800:
                            log.info('[AP] Видео весит более 50 МиБ. Добавляем ссылку на видео в текст.')
                            self.text += '\n🎥 <a href="{0}">{1[title]}</a>\n👁 {1[views]} раз(а) ⏳ {1[duration]} сек'.format(
                                video, attachment['video'])
                            del file
                            continue
                        self.videos.append(file)
                    elif soup.iframe:
                        self.text += '\n🎥 <a href="{0}">{1[title]}</a>\n👁 {1[views]} раз(а) ⏳ {1[duration]} сек'.format(
                            video, attachment['video'])
            self.text += '\n\n'

    def generate_music(self):
        if 'audio' in self.attachments_types:
            log.info('[AP] Извлечение аудио...')
            n = 0
            self.session.http.cookies.update(dict(remixmdevice=self.remixmdevice))
            user_id = self.api_vk.users.get()[0]['id']
            for attachment in self.post['attachments']:
                if attachment['type'] == 'audio':
                    post_url = 'https://m.vk.com/wall%(owner_id)s_%(id)s' % self.post
                    soup = BeautifulSoup(self.session.http.get(post_url).text, 'html.parser')
                    track_list = [decode_audio_url(track.get('value'), user_id) for track in
                                  soup.find_all(type='hidden') if 'mp3' in track.get('value')]
                    dur_list = [dur.get('data-dur') for dur in soup.find_all('div') if dur.get('data-dur')]
                    name = sub(r"[/\"?:|<>*]", '',
                               attachment['audio']['artist'] + ' - ' + attachment['audio']['title'] + '.mp3')
                    try:
                        file = download(track_list[n], out=name)
                    except (urllib.error.URLError, IndexError):
                        log.exception('[AP] Не удалось скачать аудиозапись. Пропускаем ее...')
                        continue
                    if getsize(file) > 52428800:
                        log.warning('[AP] Файл весит более 50 МиБ. Пропускаем его...')
                        continue
                    try:
                        music = EasyID3(file)
                    except id3.ID3NoHeaderError:
                        music = File(file, easy=True)
                        music.add_tags()
                    music['title'] = attachment['audio']['title']
                    music['artist'] = attachment['audio']['artist']
                    music.save()
                    del music
                    self.tracks.append((name, dur_list[n]))
                    n += 1

    def generate_user(self):
        if 'signer_id' in self.post:
            self.user = self.api_vk.users.get(user_ids=self.post['signer_id'], fields='domain')[0]

    def generate_repost(self):
        if self.config.getboolean('global', 'send_reposts'):
            if 'copy_history' in self.post:
                log.info('Включена отправка репоста. Начинаем парсинг репоста.')
                source_id = int(self.post['copy_history'][0]['from_id'])
                try:
                    source_info = self.api_vk.groups.getById(group_id=-source_id)[0]
                except exceptions.ApiError:
                    source_info = self.api_vk.users.get(user_ids=source_id)[0]
                repost_source = 'Репост из <a href="https://vk.com/%(screen_name)s">%(name)s</a>:\n\n' % source_info
                self.repost = VkPostParser(self.post['copy_history'][0], source_info['screen_name'], self.session,
                                           self.api_vk, self.config, True, self.what_to_parse)
                self.repost.text = repost_source
                self.repost.generate_post()


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu
