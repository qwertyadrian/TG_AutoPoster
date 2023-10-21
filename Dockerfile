FROM cicirello/pyaction:4.22.0

VOLUME /data
WORKDIR /data

COPY setup.py README.md requirements.txt ./
ADD TG_AutoPoster TG_AutoPoster
RUN pip3 --no-cache-dir install -r requirements.txt && \
    python3 setup.py install

ENTRYPOINT ["python3", "-m", "TG_AutoPoster"]
CMD []
