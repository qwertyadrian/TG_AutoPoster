import re
import subprocess
import time
from typing import List

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


def start_process(command: List) -> int:
    process = subprocess.Popen(command)
    while process.poll() is None:
        time.sleep(1)
    return process.returncode


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
        f.write(filereq.content)
    del filereq
    return file
