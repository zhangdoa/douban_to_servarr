#!/bin/bash

# Default cron schedule if not provided
: "${DOWNLOAD_CRON:=0 2,10,12,14,16,18,20,22 * * *}"

# Hardcoded config file path
CONFIG_PATH="/app/config.yml"

# Check if the configuration file is mapped
if [ ! -f "$CONFIG_PATH" ]; then
    echo "Configuration file not found at $CONFIG_PATH. Please mount your config.yml to this path."
    exit 1
fi

# Configure the cron job
echo "${DOWNLOAD_CRON} cd /app && /usr/local/bin/python /app/src/__main__.py >> /var/log/cron.log 2>&1" > /etc/cron.d/download-cron
chmod 0644 /etc/cron.d/download-cron
crontab /etc/cron.d/download-cron

# Ensure the log file exists
touch /var/log/cron.log

# Start cron and tail the log
exec "$@"
