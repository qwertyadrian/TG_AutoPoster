import re
import shutil
import subprocess
import time

from mutagen.id3 import APIC, ID3, TIT2, TPE1, error
from mutagen.mp3 import MP3
from requests import Session

# Символы, на которых можно разбить сообщение
message_breakers = ["\n", ", "]


def update_parameter(config, section, name, num, config_path="../config.ini") -> int:
    config.set(section, name, str(num))
    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)
    return num


def split(text: str, max_message_length: int = 4091) -> list:
    """Разделение текста на части

    :param text: Разбиваемый текст
    :param max_message_length: Максимальная длина разбитой части текста
    """
    if len(text) >= max_message_length:
        last_index = max(map(lambda separator: text.rfind(separator, 0, max_message_length), message_breakers))
        good_part = text[:last_index]
        bad_part = text[last_index + 1 :]
        return [good_part] + split(bad_part, max_message_length)
    else:
        return [text]


def list_splitter(lst: list, n: int) -> list:
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def start_process(command: list) -> int:
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
                desc=u"Cover",
                data=open(track_cover, "rb").read(),
            )
        )

    audio.tags.add(TIT2(encoding=3, text=title))

    audio.tags.add(TPE1(encoding=3, text=artist))

    audio.save()
    return True


def download_video(session: Session, link: str):
    filereq = session.get(link, stream=True)
    res = re.findall(r"id=(\d*)(&type)?", link)
    if res:
        file = res[0][0] + ".mp4"
    else:
        file = re.findall(r"\/(.*)\/(.*)\?", link)[0][1]
    with open(file, "wb") as receive:
        shutil.copyfileobj(filereq.raw, receive)
    del filereq
    return file
