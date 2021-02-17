FROM python:3.7
LABEL net.juniper.vendor "Juniper Networks"
LABEL description "config backup automation"

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["uwsgi", "--socket", "0.0.0.0:5000", "--protocol=http", "-w", "wsgi:app"]