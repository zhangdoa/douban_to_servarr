FROM python:3.8.12-slim
LABEL title="Douban to Servarr"
LABEL description="An automated scraper tool to send entries from your Douban lists to Servarr servers."
LABEL authors="zhangdoa"

ENV DOWNLOAD_CRON='0 2,10,12,14,16,19,21 * * *'  
COPY src /app/src
COPY requirements.txt /app
COPY user_config.yml /app
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y tzdata \
    && apt-get install -y cron \
    && ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip \
    && pip install -r requirements.txt

RUN echo "$DOWNLOAD_CRON /usr/local/bin/python /app/__main__.py -w /data >> /var/log/cron.log 2>&1" > /etc/cron.d/download-cron
RUN chmod +x /etc/cron.d/download-cron
RUN crontab /etc/cron.d/download-cron
RUN touch /var/log/cron.log
CMD python /app/src/__main__.py -w /data && cron && tail -f /var/log/cron.log