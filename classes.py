import urllib
from settings import config, audio, api_vk
from wget import download
from re import sub
from mutagen.easyid3 import EasyID3
from mutagen import id3, File


class Post:
    def __init__(self, post, group):
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
                        self.text += '\n[%(title)s](%(url)s)' % attachment['link']
            if config.getboolean('global', 'sign') and self.user:
                self.text += '\nАвтор поста: [%(first_name)s %(last_name)s](https://vk.com/%(domain)s)' % self.user
                self.text += '\nОригинал поста: [ссылка](https://vk.com/wall%(owner_id)s_%(id)s)' % self.post
    
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
                    self.photos.append({'media': open(download(photo), 'rb'), 'type': 'photo'})
    
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
                    video = 'https://vk.com/video%(owner_id)s_%(id)s' % attachment['video']
                    self.videos.append(video)

    def generate_music(self):
        if 'attachments' in self.post:
            for attachment in self.post['attachments']:
                if attachment['type'] == 'audio':
                    track = attachment['audio']['artist'] + ' - ' + attachment['audio']['title']
                    try:
                        track_list = audio.search(q=track)
                    except TypeError:
                        continue
                    for k in track_list:
                        k_artist = sub(r"[^A-Za-zА-Яа-я()'-]", '', k['artist']).lower()
                        k_title = sub(r"[^A-Za-zА-Яа-я()'-]", '', k['title']).lower()
                        i_artist = sub(r"[^A-Za-zА-Яа-я()'-]", '', attachment['audio']['artist']).lower()
                        i_title = sub(r"[^A-Za-zА-Яа-я()'-]", '', attachment['audio']['title']).lower()
                        if k_artist == i_artist and k_title == i_title:
                            name = sub(r"[/\"?:|<>*]", '', k['artist'] + ' - ' + k['title'] + '.mp3')
                            try:
                                file = download(k['url'], out=name)
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
                            self.tracks.append(name)
                            break

    def generate_user(self):
        if 'signer_id' in self.post:
            self.user = api_vk.users.get(user_ids=self.post['signer_id'], fields='domain')[0]
