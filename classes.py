from config import config
from wget import download


class Post:
    text = None
    photos = []
    tracks = []
    docs = []
    videos = []
    user = None
    user_link = None

    def __init__(self, post, group):
        self.pattern = '@' + config.get(group, 'domain')
        self.post = post
        self.text = None
        self.user = None
        self.user_link = None
        self.photos = []
        self.videos = []
        self.docs = []
        self.tracks = []

    def generate_post(self):
        pass

    def generate_text(self):
        if self.post['text']:
            self.text = self.post['text']
            self.text = self.text.replace(self.pattern, '')
            if 'attachments' in self.post:
                for attachment in self.post['attachments']:
                    if attachmemt['type'] == 'link':
                        self.text += '\n[%(title)s](%(link)s)' % attachment['link']
            if config.get('global', 'post_author') and self.users:
                self.text += '\n%s ' % config.get('settings', 'post_author') + '[%(first_name)s %(last_name)s](%(domain)s)' % self.user
            if config.get('global', 'post_link'):
                self.text += '\n[%s](%s)' % (config.get('global', 'post_link'), self.link)
    
    def generate_photos(self):
        if 'attachments' in self.post:
            for attachment in self.post['attachmemts']:
                if attachment['type'] == 'photo':
                    photo = i['photo']['photo_75']
                    try:
                        photo = i['photo']['photo_130']
                        photo = i['photo']['photo_604']
                        photo = i['photo']['photo_807']
                        photo = i['photo']['photo_1280']
                        photo = i['photo']['photo_2560']
                    except KeyError:
                        pass
                    self.photos.append({'media': open(download(photo), 'rb'), 'type': 'photo'})
    
    def generate_docs(self):
        if 'attachments' in self.post:
            for attachment in self.post['attachmemts']:
                if attachment['type'] == 'doc':
                    if attachment['doc']['size'] < 52428800:
                        doc = (download('%(url)s', out='file') + '.%(ext)s')  % attachment['doc']
                        self.docs.append(doc, 'rb')
    
    def generate_videos(self):
        if 'attachments' in self.post:
            for attachment in self.post['attachments']:
                if attachment['type'] == 'video':
                    video = 'https://vk.com/video%(owner_id)s_%(id)s' % attachment['video']
                    self.videos.append(video)
                        
                    
