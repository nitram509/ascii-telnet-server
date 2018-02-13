FROM python:2.7-alpine
MAINTAINER Manuel E. de Paz Carmona <manuel.depaz@gmail.com>

RUN mkdir /app
WORKDIR /app
COPY . /app

EXPOSE 23

CMD python ascii_telnet_server.py --stdout -f sample_movies/short_intro.txt
