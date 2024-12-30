# Use a slim Python base image
FROM python:3.10.6-slim

# Metadata
LABEL title="Douban to Servarr"
LABEL description="An automated scraper tool to send entries from your Douban lists to Servarr servers."
LABEL authors="zhangdoa"

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Working directory
WORKDIR /app

# Copy application code and requirements
COPY src /app/src
COPY requirements.txt /app

# Install dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        zlib1g-dev \
        tzdata \
        libxml2-dev \
        libxslt-dev \
        python3-dev \
        cron \
    && ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
