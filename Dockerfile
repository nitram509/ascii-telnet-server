FROM python:3.7-alpine

ENV mode stdout
ENV input_file sample_movies/short_intro.txt

RUN mkdir /app
WORKDIR /app
COPY . /app

EXPOSE 23

CMD python ascii_telnet_server.py --$mode -f $input_file && echo ""
