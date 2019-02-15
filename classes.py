import urllib
import sys
from os.path import getsize
from settings import config, api_vk, session
from botlogs import log
from wget import download
from re import sub, compile, finditer, MULTILINE
from mutagen.easyid3 import EasyID3
from mutagen import id3, File
from telegram import InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from bs4 import BeautifulSoup
from pytube import YouTube
from vk_api.audio_url_decoder import decode_audio_url
from vk_api import exceptions


class Post:
    def __init__(self, post, group):
        self.youtube_link = 'https://youtube.com/watch?v='
        self.regex = compile(r'/(\S*?)\?')
        self.remixmdevice = '1920/1080/1/!!-!!!!'
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

    def generate_post(self):
        log.info('[AP] Начало извлечения содержимого поста...')
        if config.getboolean('global', 'sign_posts'):
            self.generate_user()
        self.generate_text()
        self.generate_photos()
        self.generate_docs()
        self.generate_videos()
        self.generate_music()
        self.generate_repost()

    def generate_text(self):
        if self.post['text']:
            log.info('[AP] Обнаружен текст. Извлечение...')
            self.text += self.post['text']
            self.text = self.text.replace(self.pattern, '')
            post = 'https://vk.com/wall%(owner_id)s_%(id)s' % self.post
            if 'attachments' in self.post:
                for attachment in self.post['attachments']:
                    if attachment['type'] == 'link':
                        self.text += '\n<a href="%(url)s">%(title)s</a>' % attachment['link']
                        # self.text += '\n[%(title)s](%(url)s)' % attachment['link']
            if config.getboolean('global', 'sign_posts') and self.user:
                log.info('[AP] Подписывание поста и добавление ссылки на его оригинал.')
                user = 'https://vk.com/%(domain)s' % self.user
                button_list = [InlineKeyboardButton('Автор поста: %(first_name)s %(last_name)s' % self.user, url=user),
                               InlineKeyboardButton('Оригинал поста', url=post)]
                self.reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
            elif config.getboolean('global', 'sign_posts') and not self.user:
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

    def generate_photos(self):
        if 'attachments' in self.post:
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
        if 'attachments' in self.post:
            log.info('[AP] Извлечение вложениий (файлы, гифки и т.п.)...')
            for attachment in self.post['attachments']:
                if attachment['type'] == 'doc' and attachment['doc']['size'] < 52428800:
                    try:
                        doc = download(attachment['doc']['url'], out='file' + '.' + attachment['doc']['ext'])
                        self.docs.append(doc)
                    except urllib.error.URLError:
                        log.warn('[AP] Невозможно скачать вложенный файл: {0}.'.format(sys.exc_info()[1]))
    
    def generate_videos(self):
        if 'attachments' in self.post:
            log.info('[AP] Извлечение видео...')
            log.info('[AP] Данная функция находится в стадии тестирования. В некоторых видео может быть только звук, а может вообще не запуститься.')
            for attachment in self.post['attachments']:
                if attachment['type'] == 'video':
                    video = 'https://m.vk.com/video%(owner_id)s_%(id)s' % attachment['video']
                    soup = BeautifulSoup(session.http.get(video).text, 'html.parser')
                    if soup.find_all('source'):
                        video_link = soup.find_all('source')[1].get('src')
                        file = download(video_link)
                        if getsize(file) > 52428800:
                            del file
                            continue
                        self.videos.append(file)
                    elif soup.iframe:
                        try:
                            video_id = self.regex.findall(soup.iframe['src'])[0].split('/')[3]
                            yt = YouTube(self.youtube_link + video_id)
                        except:
                            continue
                        for stream in yt.streams.all():
                            if stream.filesize <= 52428800 and ('.mp4' in stream.default_filename):
                                file = stream.default_filename
                                stream.download()
                                self.videos.append(file)
                                break

    def generate_music(self):
        if 'attachments' in self.post:
            log.info('[AP] Извлечение аудио...')
            log.info('[AP] Данная функция находится в стадии тестирования.')
            n = 0
            session.http.cookies.update(dict(remixmdevice=self.remixmdevice))
            user_id = api_vk.users.get()[0]['id']
            for attachment in self.post['attachments']:
                if attachment['type'] == 'audio':
                    post_url = 'https://m.vk.com/wall%(owner_id)s_%(id)s' % self.post
                    soup = BeautifulSoup(session.http.get(post_url).text, 'html.parser')
                    track_list = [decode_audio_url(track.get('value'), user_id) for track in soup.find_all(type='hidden') if 'mp3' in track.get('value')]
                    dur_list = [dur.get('data-dur') for dur in soup.find_all('div') if dur.get('data-dur')]
                    name = sub(r"[/\"?:|<>*]", '', attachment['audio']['artist'] + ' - ' + attachment['audio']['title'] + '.mp3')
                    try:
                        file = download(track_list[n], out=name)
                    except (urllib.error.URLError, IndexError):
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
            self.user = api_vk.users.get(user_ids=self.post['signer_id'], fields='domain')[0]

    def generate_repost(self):
        if config.getboolean('global', 'send_reposts'):
            if 'copy_history' in self.post:
                source_id = int(self.post['copy_history'][0]['from_id'])
                try:
                    source_info = api_vk.groups.getById(group_id=-source_id)[0]
                except exceptions.ApiError:
                    source_info = api_vk.users.get(user_ids=source_id)[0]
                repost_source = 'Репост из <a href="https://vk.com/%(screen_name)s">%(name)s</a>:\n\n' % source_info
                self.repost = Post(self.post['copy_history'][0], source_info['screen_name'])
                self.repost.text = repost_source
                self.repost.generate_post()


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu
