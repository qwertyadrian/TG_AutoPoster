import binascii
import os
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

import m3u8
from Crypto.Cipher import AES
from moviepy.audio.io.AudioFileClip import AudioClip, AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from mutagen.id3 import APIC, ID3, TIT2, TPE1, error
from mutagen.mp3 import MP3
from requests import Session


class Attachments:
    def __init__(self):
        self.media = []
        self.audio = []
        self.documents = []

    def all(self):
        return self.media + self.audio + self.documents

    def __len__(self):
        return len(self.all())

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.all()[item]
        elif item == "media":
            return self.media
        elif item == "audio":
            return self.audio
        elif item == "docs" or item == "documents":
            return self.documents
        else:
            raise KeyError(f"Key {item} not found")


def add_audio_tags(filename, artist, title, track_cover):
    audio = MP3(filename, ID3=ID3)
    # add ID3 tag if it doesn't exist
    try:
        audio.add_tags()
    except error as e:
        if str(e) != "an ID3 tag already exists":
            return False
    audio.clear()

    if track_cover:
        audio.tags.add(
            APIC(
                encoding=3,  # 3 is for utf-8
                mime="image/png",  # image/jpeg or image/png
                type=3,  # 3 is for the cover image
                desc="Cover",
                data=open(track_cover, "rb").read(),
            )
        )

    audio.tags.add(TIT2(encoding=3, text=title))

    audio.tags.add(TPE1(encoding=3, text=artist))

    audio.save()
    return True


def download_video(session: Session, link: str) -> str:
    filereq = session.get(link, stream=True)
    res = re.findall(r"id=(\d*)(&type)?", link)
    if res:
        file = res[0][0] + ".mp4"
    else:
        file = re.findall(r"/(.*)/(.*)\?", link)[0][1]
    with open(file, "wb") as f:
        for chunk in filereq.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return file


def get_key(data):
    for i in range(data.media_sequence):
        try:
            key_uri = data.keys[i].uri
            host_uri = "/".join(key_uri.split("/")[:-1])
            return host_uri
        except Exception:
            continue


def read_keys(path):
    data_response = urlopen(path)
    content = data_response.read()
    return content


def get_ts(url):
    data = m3u8.load(url)
    key_link = get_key(data)
    ts_content = b""
    key = None

    for i, segment in enumerate(data.segments):
        decrypt_func = lambda x: x
        if segment.key.method == "AES-128":
            if not key:
                key_uri = segment.key.uri
                key = read_keys(key_uri)
            ind = i + data.media_sequence
            iv = binascii.a2b_hex("%032x" % ind)
            cipher = AES.new(key, AES.MODE_CBC, iv=iv)
            decrypt_func = cipher.decrypt

        ts_url = f"{key_link if key_link else segment.key.base_uri}/{segment.uri}"
        coded_data = read_keys(ts_url)
        ts_content += decrypt_func(coded_data)
    return ts_content


def m3u8_to_mp3(url, name):
    ts_content = get_ts(url)
    if ts_content is None:
        raise TypeError("Empty mp3 content to save.")

    tmp_file = NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp_file.write(ts_content)
    tmp_file.close()

    audioclip = AudioFileClip(tmp_file.name)
    audioclip.write_audiofile(name, bitrate='3000k')
    audioclip.close()
    os.unlink(tmp_file.name)


def gif_to_video(path):
    result = path.replace(".gif", ".mp4")
    videoclip = VideoFileClip(path)

    make_frame = lambda t: 2 * [0.0]
    audioclip = AudioClip(make_frame, duration=videoclip.duration)
    videoclip = videoclip.set_audio(audioclip)
    videoclip.write_videofile(result)

    return result
