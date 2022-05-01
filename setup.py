#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = "2.4.3"

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="TG_AutoPoster",
    version=version,

    author="qwertyadrian",
    author_email="me@qwertyadrian.ru",

    description="Telegram Bot for AutoPosting from VK",
    long_description=long_description,
    long_description_content_type='text/markdown',

    url="https://github.com/qwertyadrian/TG_AutoPoster",
    download_url="https://github.com/qwertyadrian/TG_AutoPoster/archive/v{}.zip".format(
        version
    ),

    license="MIT License, see LICENCE.md",
    platforms=["OS Independent"],

    packages=find_packages(),
    install_requires=[
        "pyrogram==2.0.16",
        "tgcrypto",
        "loguru==0.6.0",
        "wget==3.2",
        "mutagen==1.45.1",
        "beautifulsoup4==4.11.1",
        "vk_api==11.9.7",
        "streamlink==4.0.0",
    ],

    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Communications :: Chat",
    ]
)
