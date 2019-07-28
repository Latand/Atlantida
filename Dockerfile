FROM python:latest

RUN mkdir /src
WORKDIR /src
COPY requirements.txt /src/
COPY init.sql /src/
RUN pip install -r requirements.txt

ADD init.sql /docker-entrypoint-initdb.d
COPY . /src