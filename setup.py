#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from setuptools import setup, find_packages


with open("requirements.txt", encoding="utf-8") as r:
    requires = [i.strip() for i in r]

with open("TG_AutoPoster/__init__.py", encoding="utf-8") as f:
    version = re.findall(r"__version__ = \"(.+)\"", f.read())[0]

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="TG_AutoPoster",
    version=version,

    author="qwertyadrian",
    author_email="me@qwertyadrian.ru",

    description="Telegram Bot for reposting from VK",
    long_description=long_description,
    long_description_content_type='text/markdown',

    url="https://github.com/qwertyadrian/TG_AutoPoster",
    download_url="https://github.com/qwertyadrian/TG_AutoPoster/releases/latest",

    license="MIT License",
    platforms=["OS Independent"],

    packages=find_packages(),
    install_requires=requires,

    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet",
        "Topic :: Communications",
        "Topic :: Communications :: Chat",
    ],
    python_requires="~=3.7",
)
