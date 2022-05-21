FROM python:3-alpine

VOLUME /data
WORKDIR /data

COPY TG_AutoPoster setup.py README.md requirements.txt ./
RUN apk add --no-cache ffmpeg gcc musl-dev libxml2-dev libxslt-dev && \
    pip3 --no-cache-dir install -r requirements.txt && \
    python3 setup.py install && \
    apk del -r gcc musl-dev libxml2-dev libxslt-dev

ENTRYPOINT ["python3", "-m", "TG_AutoPoster"]
CMD []