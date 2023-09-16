import os
import datetime
import json
from loguru import logger
from douban.douban import DoubanMovieCrawler
from douban.douban import DoubanMusicCrawler
from radarr.radarr import Radarr
from sonarr.sonarr import Sonarr
from lidarr.lidarr import Lidarr


class ListParser:
    def __init__(self, **kwargs):
        self.workdir = kwargs["workdir"]
        self.douban_config = kwargs["douban"]
        self.movie_crawler = DoubanMovieCrawler("movie", self.douban_config["cookies"])
        self.music_crawler = DoubanMusicCrawler("music", self.douban_config["cookies"])
        self.radarr = Radarr(
            host=kwargs["radarr"]["host"],
            port=kwargs["radarr"]["port"],
            url_base=kwargs["radarr"]["url_base"],
            api_key=kwargs["radarr"]["api_key"],
            is_https=kwargs["radarr"]["https"],
            rootFolderPath=kwargs["radarr"]["rootFolderPath"],
            monitored=kwargs["radarr"]["monitored"],
            addOptions=kwargs["radarr"]["addOptions"],
            qualityProfileId=kwargs["radarr"]["qualityProfileId"],
            minimumAvailability=kwargs["radarr"]["minimumAvailability"],
        )
        self.sonarr = Sonarr(
            host=kwargs["sonarr"]["host"],
            port=kwargs["sonarr"]["port"],
            url_base=kwargs["sonarr"]["url_base"],
            api_key=kwargs["sonarr"]["api_key"],
            is_https=kwargs["sonarr"]["https"],
            rootFolderPath=kwargs["sonarr"]["rootFolderPath"],
            monitored=kwargs["sonarr"]["monitored"],
            addOptions=kwargs["sonarr"]["addOptions"],
            qualityProfileId=kwargs["sonarr"]["qualityProfileId"],
            languageProfileId=kwargs["sonarr"]["languageProfileId"],
            seriesType=kwargs["sonarr"]["seriesType"],
            addSeasonSubfolder=kwargs["sonarr"]["addSeasonSubfolder"],
            genreSubfolderPath=kwargs["sonarr"]["genreSubfolderPath"],
        )
        self.lidarr = Lidarr(
            host=kwargs["lidarr"]["host"],
            port=kwargs["lidarr"]["port"],
            url_base=kwargs["lidarr"]["url_base"],
            api_key=kwargs["lidarr"]["api_key"],
            is_https=kwargs["lidarr"]["https"],
            rootFolderPath=kwargs["lidarr"]["rootFolderPath"],
            monitored=kwargs["lidarr"]["monitored"],
            addOptions=kwargs["lidarr"]["addOptions"],
            qualityProfileId=kwargs["lidarr"]["qualityProfileId"],
        )

    def start(self):
        logger.info(
            "Starting at {}.",
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        users = self.douban_config["user_domain"]
        categories = self.douban_config["categories"]
        for u in users:
            if u == "":
                continue
            for category in categories:
                if category == "":
                    continue
                self.process_user_lists(
                    u,
                    category,
                    list_types=self.douban_config["list_types"],
                    start_date=self.douban_config["start_date"],
                    end_date=self.douban_config["end_date"],
                    start_page=self.douban_config["start_page"],
                    mode=self.douban_config["mode"],
                    instant_add=self.douban_config["instant_add"],
                    list_file_path=self.douban_config["list_file_path"],
                )
        logger.info("The scraper finished all tasks.")

    def process_user_lists(
        self,
        user_id,
        category,
        list_types,
        start_date,
        end_date,
        start_page,
        mode="scrape_and_add",
        instant_add=True,
        list_file_path="",
    ):
        entry_details_lists = self.get_entry_details_lists(
            user_id,
            category,
            list_types,
            start_date,
            end_date,
            start_page,
            mode,
            instant_add,
            list_file_path,
        )

        if (
            entry_details_lists is not None
            and instant_add == False
            and mode != "scrape_only"
        ):
            for list_type in list_types:
                for entry_details in entry_details_lists[list_type]:
                    self.add_entry(entry_details, list_type)

    def get_entry_details_lists(
        self,
        user_id,
        category,
        list_types,
        start_date,
        end_date,
        start_page,
        mode,
        instant_add,
        list_file_path,
    ):
        user_entries_lists = {}
        entry_details_lists = {}

        if mode == "add_from_file":
            user_entries_lists, entry_details_lists = self.load_lists(list_file_path)
            if len(entry_details_lists) > 0:
                return entry_details_lists

            if len(user_entries_lists) > 0:
                logger.info(
                    "The user entries list {} of user {} has been load.",
                    list_file_path,
                    user_id,
                )
            else:
                logger.warning(
                    "The loaded list file {} is empty for user {}.",
                    list_file_path,
                    user_id,
                )
                return None

        crawler = None
        if category == "movie":
            crawler = self.movie_crawler
        elif category == "music":
            crawler = self.music_crawler

        if len(user_entries_lists) == 0:
            user_entries_lists = crawler.get_user_entry_lists(
                user_id,
                list_types=list_types,
                start_date=start_date,
                end_date=end_date,
                start_page=start_page,
            )
            if user_entries_lists is None or len(user_entries_lists) == 0:
                logger.info(
                    "There is nothing to add from the list(s) {} of category '{}' for user {}.",
                    list_types,
                    category,
                    user_id,
                )
                return None
            else:
                self.save_lists("user_entries", category, user_entries_lists)

        for list_type in list_types:
            entry_details_lists[list_type] = []
            if list_type not in user_entries_lists:
                logger.info("List type {} doesn't exist, skip to the next.", list_type)
                continue
            logger.info('Processing list: "{}"...', list_type)
            for user_entry in user_entries_lists[list_type]:
                entry_details = crawler.get_details_by_id(user_entry["id"])
                if entry_details is None:
                    logger.warning(
                        'Failed to scrape: "{}" (id: {}).',
                        user_entry["titles"],
                        user_entry["id"],
                    )
                    continue
                entry_details["titles"] = user_entry["titles"]
                entry_details_lists[list_type].append(entry_details)
                if instant_add:
                    self.add_entry(entry_details, list_type)

        if len(entry_details_lists) > 0:
            self.save_lists("entry_details", category, entry_details_lists)
        return entry_details_lists

    def load_lists(self, list_file_path):
        user_entries_lists = {}
        entry_details_lists = {}
        with open(list_file_path, "r", encoding="utf-8") as file:
            loaded_list = json.load(file)
            if "user_entries" in list_file_path:
                user_entries_lists = loaded_list
            elif "entry_details" in list_file_path:
                entry_details_lists = loaded_list
            else:
                logger.error(
                    "Trying to load an unsupported list file '{}'.",
                    list_file_path,
                )
        return [user_entries_lists, entry_details_lists]

    def save_lists(self, file_type, category, lists):
        dir_name = "lists"
        cwd = os.getcwd()
        dir_path = cwd + os.sep + dir_name
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        file_name = (
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            + "_%s" % file_type
            + "_%s" % category
            + ".list"
        )
        file_path = dir_path + os.sep + file_name

        logger.info("Saving the '{}_{}' list to {}.", file_type, category, file_path)
        with open(file_path, "w", encoding="utf-8") as list_file:
            json_obj = json.dumps(lists, indent=4, sort_keys=True)
            list_file.write(json_obj)

    def add_entry(self, entry_details, list_type):
        type = entry_details["type"]
        if "Series" == type:
            self.sonarr.try_to_add_item(entry_details, list_type)
        elif "Movie" == type:
            self.radarr.try_to_add_item(entry_details, list_type)
        # elif "Book" == type: # TODO: Implement this
        elif "Music" == type:
            self.lidarr.try_to_add_item(entry_details, list_type)
