FROM python:3

VOLUME /data
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -fr /var/lib/apt/lists /var/lib/cache/* /var/log/*
RUN pip3 --no-cache-dir install 'TG-AutoPoster'

WORKDIR /data
ENTRYPOINT ["python3", "-m", "TG_AutoPoster"]
CMD []