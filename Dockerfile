FROM python:3
#ENV TERM=xterm
VOLUME /TG_AutoPoster
ADD requirements.txt /
#RUN apt update && apt install -y nano && apt clean
RUN pip3 --no-cache-dir install -r requirements.txt
COPY ["handlers.py", "parser.py", "sender.py", "sender.py", "TG_AutoPoster.py", "TG_AutoPoster.sh", "tools.py", "__init__.py", "/TG_AutoPoster/"]
#COPY TG_AutoConfigurator /TG_AutoPoster/TG_AutoConfigurator
WORKDIR /TG_AutoPoster
ENTRYPOINT ["bash", "TG_AutoPoster.sh"]
CMD ["--loop"]
