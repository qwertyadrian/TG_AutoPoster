from config import config


class Post:
    text = None
    photos = []
    tracks = []
    docs = []
    links = None
    videos = []
    user = None
    user_link = None

    def __init__(self, post, group):
        self.pattern = '@' + config.get(group, 'domain')
        self.post = post
        self.text = None
        self.links = None
        self.user = None
        self.user_link = None
        self.photos = []
        self.videos = []
        self.docs = []
        self.docs = []

    def generate_post(self):
        pass

    def generare_text(self):
        if self.post['text']:
            self.text = self.post['text']
            self.text = self.text.replace(self.pattern, '')
