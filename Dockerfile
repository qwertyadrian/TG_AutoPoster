FROM python:3.12-slim

VOLUME /data
WORKDIR /data

COPY setup.py README.md requirements.txt ./
ADD TG_AutoPoster TG_AutoPoster
ADD vk_api vk_api

RUN apt-get update && apt-get install gcc -y \
                                                && pip install --no-cache-dir setuptools
RUN pip --no-cache-dir install -r requirements.txt && \
    python setup.py install

ENTRYPOINT ["python3", "-m", "TG_AutoPoster"]
CMD []
