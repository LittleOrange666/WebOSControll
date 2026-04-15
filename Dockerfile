FROM python:3.12-alpine

WORKDIR /app

ARG TZ_LOCATION=Asia/Taipei

RUN apk add --no-cache tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ_LOCATION /etc/localtime && \
    echo "$TZ_LOCATION" > /etc/timezone

ENV TZ=$TZ_LOCATION

COPY requirements.txt /app/

RUN pip3 install -r requirements.txt

COPY bot.py /app/
COPY modules /app/modules

CMD ["python3", "bot.py"]