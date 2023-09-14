import os
import sys
import argparse
import datetime
import yaml
from loguru import logger
from list_parser import ListParser

user_setting_name = "user_config.yml"


def load_user_config(workdir):
    user_config_file_path = workdir + os.sep + user_setting_name
    if not os.path.exists(user_config_file_path):
        logger.warning(
            "File user_config.xml doesn't exist. Please create one from user_config_template.xml."
        )
        return None
    with open(user_config_file_path, "r", encoding="utf-8") as file:
        user_config = yaml.safe_load(file)
    return user_config


def create_bot(user_config, workdir):
    within_days = 0
    if user_config["douban"].get("within_days"):
        within_days = user_config["douban"]["within_days"]
    if within_days == 0:
        from_date = user_config["douban"]["from_date"]
        to_date = user_config["douban"]["to_date"]
        if from_date == "today":
            from_date = datetime.date.today()
        if to_date == "epoch":
            to_date = datetime.date(1970, 1, 1)
        within_days = (from_date - to_date).days

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
            "user_domain": user_config["douban"]["user_domain"].split(";"),
            "within_days": within_days,
            "turn_page": user_config["douban"]["turn_page"],
            "categories": user_config["douban"]["categories"].split(";"),
            "list_types": user_config["douban"]["list_types"].split(";"),
            "save_scraped_list": user_config["douban"]["save_scraped_list"],
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
        },
    }
    return ListParser(**params)


if __name__ == "__main__":
    # 运行在docker上的时候，workdir = '/data',记得修改, 本地运行 workdir = os.getcwd()
    workdir = os.getcwd()
    if not os.path.exists(workdir):
        logger.error("请提供正确的配置，工作目录不存在：{}", workdir)
        sys.exit()
    user_config = load_user_config(workdir)
    if user_config:
        logger.add(
            sys.stdout,
            format="{time} {level} {message}",
            filter="my_module",
            level=user_config["global"]["log_level"],
        )
        logger.add("movie_robot_{time}.log")

        movie_bot = create_bot(user_config, workdir)
        if movie_bot:
            movie_bot.start()
        else:
            logger.error(
                "Something isn't correct, please check the console output for the details"
            )
