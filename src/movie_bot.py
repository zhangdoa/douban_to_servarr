import datetime
import json
from loguru import logger
from douban.douban import DoubanMovieCrawler
from radarr.radarr import Radarr
from sonarr.sonarr import Sonarr


class MovieBot:
    def __init__(self, **kwargs):
        self.workdir = kwargs["workdir"]
        self.douban_config = kwargs["douban"]
        self.crawler = DoubanMovieCrawler(self.douban_config["cookies"])
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

    def start(self):
        logger.info(
            "开始寻找影视并自动添加，现在时间是 {}",
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        users = self.douban_config["user_domain"]
        for u in users:
            if u != "":
                self.search_and_add(
                    u,
                    list_types=self.douban_config["types"],
                    within_days=self.douban_config["within_days"],
                    turn_page=self.douban_config["turn_page"],
                    mode=self.douban_config["mode"],
                    save_fetched_list=self.douban_config["save_fetched_list"],
                    saved_fetched_list=self.douban_config["saved_fetched_list"],
                )
        logger.info("所有用户的影视添加已经完成")

    def search_and_add(
        self,
        user_id,
        list_types=["wish"],
        within_days=365,
        turn_page=True,
        mode="fetch_and_add",
        save_fetched_list=True,
        saved_fetched_list="",
    ):
        movie_details_lists = self.get_movie_details_lists(
            user_id, list_types, within_days, turn_page, mode, saved_fetched_list
        )

        if mode != "add_from_file" and save_fetched_list:
            self.save_movie_details_list(movie_details_lists)

        if mode != "fetch_only":
            self.add_movies(list_types, movie_details_lists)

    def get_movie_details_lists(
        self, user_id, list_types, within_days, turn_page, mode, saved_fetched_list
    ):
        movie_details_lists = {}
        if mode == "add_from_file":
            with open(saved_fetched_list, "r", encoding="utf-8") as file:
                movie_details_lists = json.load(file)
        else:
            user_movie_lists = self.crawler.get_user_movie_lists(
                user_id,
                list_types=list_types,
                within_days=within_days,
                turn_page=turn_page,
            )
            if user_movie_lists is None or len(user_movie_lists) == 0:
                logger.info("{}没有任何影视资源需要添加", user_id)
                return None

            for list_type in list_types:
                movie_details_lists[list_type] = []
                logger.info("Processing list: {}...", list_type)
                for user_movie in user_movie_lists[list_type]:
                    movie_details = self.crawler.get_movie_details_by_id(
                        user_movie["id"]
                    )
                    if movie_details is None:
                        logger.warning(
                            "信息获取异常: {}(id: {})", user_movie["title"], user_movie["id"]
                        )
                        continue
                    logger.info(
                        "The details of 《{}》 (original_title: {}, imdb_id: {}) has been fetched",
                        user_movie["title"],
                        user_movie["original_title"],
                        movie_details["imdb_id"],
                    )
                    movie_details_lists[list_type].append(movie_details)
        return movie_details_lists

    def add_movies(self, list_types, movie_details_lists):
        for list_type in list_types:
            for movie_details in movie_details_lists[list_type]:
                self.add_movie(movie_details, list_type)

    def add_movie(self, movie_details, list_type):
        type = movie_details["type"]
        is_series = "Series" == type
        if is_series:
            self.sonarr.try_to_add_item(movie_details, list_type)
        else:
            self.radarr.try_to_add_item(movie_details, list_type)

    def save_movie_details_list(self, movie_details_lists):
        file_name = (
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_fetched_list.json"
        )
        logger.info("Saving the fetched list to {}", file_name)
        with open(file_name, "w", encoding="utf-8") as fetched_list_file:
            json_obj = json.dumps(movie_details_lists, indent=4, sort_keys=True)
            fetched_list_file.write(json_obj)
