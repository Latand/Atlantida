FROM python:latest

RUN mkdir /src
WORKDIR /src
COPY requirements.txt /src/
COPY init.sql /src/
RUN pip install -r requirements.txt
#RUN mysql -u root --password=vos92dbsVGS2v4v < mysql_scripts/init.sql
#docker exec -i database-test mysql -u root --password=vos92dbsVGS2v4v < mysql_scripts/init.sql

ADD init.sql /docker-entrypoint-initdb.d
COPY . /src