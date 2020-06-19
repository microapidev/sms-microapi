FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1

ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /sms_api

WORKDIR /sms_api

ADD . /sms_api

RUN pip install -r requirements.txt