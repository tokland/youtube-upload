FROM python:2

MAINTAINER Marcelo Almeida <ms.almeida86@gmail.com>

RUN pip install --upgrade google-api-python-client progressbar2

WORKDIR app

COPY . /app

CMD ["/usr/local/bin/python", "bin/youtube-upload"]
