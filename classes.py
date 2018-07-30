import urllib
from os.path import getsize
from settings import config, api_vk, session
from wget import download
from re import sub, compile
from mutagen.easyid3 import EasyID3
from mutagen import id3, File
from telegram.files.inputmediaphoto import *
from bs4 import BeautifulSoup
from pytube import YouTube
from vk_api.audio_url_decoder import decode_audio_url


class Post:
    def __init__(self, post, group):
        self.youtube_link = 'https://youtube.com/watch?v='
        self.regex = compile(r'/(\S*?)\?')
        self.remixmdevice = '1920/1080/1/!!-!!!!'
        self.pattern = '@' + group
        self.post = post
        self.text = None
        self.user = None
        self.links = None
        self.photos = []
        self.videos = []
        self.docs = []
        self.tracks = []

    def generate_post(self):
        self.generate_user()
        self.generate_text()
        self.generate_photos()
        self.generate_docs()
        self.generate_videos()
        self.generate_music()

    def generate_text(self):
        if self.post['text']:
            self.text = self.post['text']
            self.text = self.text.replace(self.pattern, '')
            if 'attachments' in self.post:
                for attachment in self.post['attachments']:
                    if attachment['type'] == 'link':
                        self.text += '\n<a href="%(url)s">%(title)s</a>' % attachment['link']
                        # self.text += '\n[%(title)s](%(url)s)' % attachment['link']
            if config.getboolean('global', 'sign') and self.user:
                # Markdown Parsing
                # self.text += '\nАвтор поста: [%(first_name)s %(last_name)s](https://vk.com/%(domain)s)' % self.user
                # self.text += '\nОригинал поста: [ссылка](https://vk.com/wall%(owner_id)s_%(id)s)' % self.post
                # HTML Parsing
                self.text += '\nАвтор поста: <a href="https://vk.com/%(domain)s">%(first_name)s %(last_name)s</a>' % self.user
                self.text += '\nОригинал поста: <a href="https://vk.com/wall%(owner_id)s_%(id)s">ссылка</a>' % self.post
            elif config.getboolean('global', 'sign') and not self.user:
                # Markdown Parsing
                # self.text += '\nОригинал поста: [ссылка](https://vk.com/wall%(owner_id)s_%(id)s)' % self.post
                # HTML Parsing
                self.text += '\nОригинал поста: <a href="https://vk.com/wall%(owner_id)s_%(id)s">ссылка</a>' % self.post
    
    def generate_photos(self):
        if 'attachments' in self.post:
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
            for attachment in self.post['attachments']:
                if attachment['type'] == 'doc' and attachment['doc']['size'] < 52428800:
                    doc = download(attachment['doc']['url'], out='file' + '.' + attachment['doc']['ext'])
                    self.docs.append(doc)
    
    def generate_videos(self):
        if 'attachments' in self.post:
            for attachment in self.post['attachments']:
                if attachment['type'] == 'video':
                    video = 'https://m.vk.com/video%(owner_id)s_%(id)s' % attachment['video']
                    soup = BeautifulSoup(session.http.get(video).text, 'html.parser')
                    if soup.find_all('source'):
                        file = download(soup.find_all('source')[1].get('src'))
                        if getsize(file) > 20971520:
                            del file
                            continue
                        self.videos.append(file)
                    elif soup.iframe:
                        video_id = self.regex.findall(soup.iframe['src'])[0].split('/')[3]
                        yt = YouTube(self.youtube_link + video_id)
                        for stream in yt.streams.all():
                            if stream.filesize <= 20971520 and ('.mp4' in stream.default_filename):
                                file = stream.default_filename
                                stream.download()
                                self.videos.append(file)
                                break

    def generate_music(self):
        if 'attachments' in self.post:
            session.http.cookies.update(dict(remixmdevice=self.remixmdevice))
            for attachment in self.post['attachments']:
                if attachment['type'] == 'audio':
                    n = 0
                    post_url = 'https://m.vk.com/wall%(owner_id)s_%(id)s' % self.post
                    soup = BeautifulSoup(session.http.get(post_url).text, 'html.parser')
                    track_list = [decode_audio_url(track.get('value'), api_vk.users.get()[0]['id']) for track in soup.find_all(type='hidden') if 'mp3' in track.get('value')]
                    dur_list = [dur.get('data-dur') for dur in soup.find_all('div') if dur.get('data-dur')]
                    name = sub(r"[/\"?:|<>*]", '', attachment['audio']['artist'] + ' - ' + attachment['audio']['title'] + '.mp3')
                    try:
                        file = download(track_list[n], out=name)
                    except urllib.error.URLError:
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
