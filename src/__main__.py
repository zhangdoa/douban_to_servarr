import os
import sys
import datetime
from zoneinfo import ZoneInfo
import yaml
from loguru import logger
from list_parser import ListParser


def is_running_in_docker():
    try:
        with open("/proc/1/cgroup", "r") as f:
            if "docker" in f.read():
                return True
    except FileNotFoundError:
        return False
    return False


def load_user_config():
    if is_running_in_docker():
        config_file = "/app/config.yml"
    else:
        config_file = os.path.join(os.getcwd(), "config.yml")

    if not os.path.exists(config_file):
        logger.error(
            "Configuration file '{}' does not exist. Please ensure it is present at the expected path.",
            config_file,
        )
        return None

    try:
        with open(config_file, "r", encoding="utf-8") as file:
            user_config = yaml.safe_load(file)
        logger.info("Successfully loaded configuration from '{}'.", config_file)
        return user_config
    except yaml.YAMLError as e:
        logger.error("Failed to parse YAML file '{}': {}", config_file, e)
    except Exception as e:
        logger.error("Unexpected error loading '{}': {}", config_file, e)

    return None


def create_bot(user_config, workdir):
    max_scraping_days = user_config["douban"]["max_scraping_days"]
    start_date = user_config["douban"]["start_date"]
    if start_date == "today":
        # Douban uses CST
        start_date = datetime.datetime.now(ZoneInfo("Asia/Shanghai")).date()
    end_date = user_config["douban"]["end_date"]
    if max_scraping_days == 0:
        if end_date == "epoch":
            end_date = datetime.date(1970, 1, 1)
    else:
        end_date = start_date - datetime.timedelta(days=max_scraping_days)

    list_file_path = ""
    mode = user_config["douban"]["mode"]
    if mode == "add_from_file":
        list_file_path = user_config["douban"]["list_file_path"]
        if not list_file_path or list_file_path == "":
            logger.error(
                "{} mode is specified by the saved scraped list is not set", mode
            )
            return

    params = {
        "workdir": workdir,
        "douban": {
            "cookies": user_config["douban"]["cookies"],
            "user_domain": str(user_config["douban"]["user_domain"]).split(";"),
            "start_date": start_date,
            "end_date": end_date,
            "start_page": user_config["douban"]["start_page"],
            "categories": user_config["douban"]["categories"].split(";"),
            "list_types": user_config["douban"]["list_types"].split(";"),
            "instant_add": user_config["douban"]["instant_add"],
            "mode": user_config["douban"]["mode"],
            "list_file_path": list_file_path,
        },
        "radarr": {
            "host": user_config["radarr"]["host"],
            "port": user_config["radarr"]["port"],
            "url_base": user_config["radarr"]["url_base"],
            "api_key": user_config["radarr"]["api_key"],
            "https": user_config["radarr"]["https"],
            "rootFolderPath": user_config["radarr"]["rootFolderPath"],
            "monitored": user_config["radarr"]["monitored"],
            "qualityProfileId": user_config["radarr"]["qualityProfileId"],
            "addOptions": user_config["radarr"]["addOptions"],
            "minimumAvailability": user_config["radarr"]["minimumAvailability"],
        },
        "sonarr": {
            "host": user_config["sonarr"]["host"],
            "port": user_config["sonarr"]["port"],
            "url_base": user_config["sonarr"]["url_base"],
            "api_key": user_config["sonarr"]["api_key"],
            "https": user_config["sonarr"]["https"],
            "rootFolderPath": user_config["sonarr"]["rootFolderPath"],
            "monitored": user_config["sonarr"]["monitored"],
            "addOptions": user_config["sonarr"]["addOptions"],
            "qualityProfileId": user_config["sonarr"]["qualityProfileId"],
            "languageProfileId": user_config["sonarr"]["languageProfileId"],
            "seriesType": user_config["sonarr"]["seriesType"],
            "addSeasonSubfolder": user_config["sonarr"]["addSeasonSubfolder"],
            "genreSubfolderPath": user_config["sonarr"]["genreSubfolderPath"],
        },
        "lidarr": {
            "host": user_config["lidarr"]["host"],
            "port": user_config["lidarr"]["port"],
            "url_base": user_config["lidarr"]["url_base"],
            "api_key": user_config["lidarr"]["api_key"],
            "https": user_config["lidarr"]["https"],
            "rootFolderPath": user_config["lidarr"]["rootFolderPath"],
            "monitored": user_config["lidarr"]["monitored"],
            "addOptions": user_config["lidarr"]["addOptions"],
            "qualityProfileId": user_config["lidarr"]["qualityProfileId"],
            "metadataProfileId": user_config["lidarr"]["metadataProfileId"],
        },
    }
    return ListParser(**params)


if __name__ == "__main__":
    user_config = load_user_config()
    if user_config is None:
        sys.exit()

    logger.add(
        sys.stdout,
        format="{time} {level} {message}",
        filter="my_module",
        level=user_config["global"]["log_level"],
    )

    # Hardcoded or default log directory
    log_dir_path = os.path.abspath("./logs")

    try:
        # Create the log directory if it doesn't exist
        os.makedirs(log_dir_path, exist_ok=True)
        logger.info("Log directory set to: {}", log_dir_path)
    except PermissionError as e:
        logger.error(
            "Permission denied when creating log directory '{}': {}", log_dir_path, e
        )
        raise
    except Exception as e:
        logger.error("Failed to create log directory '{}': {}", log_dir_path, e)
        raise

    # Add file logging
    logger.add(f"{log_dir_path}{os.sep}{{time}}.log")

    # Create and start the bot
    bot = create_bot(user_config, os.getcwd())
    if bot:
        bot.start()
    else:
        logger.error(
            "Something isn't correct, please check the console output for the details."
        )
