import datetime
import json
from loguru import logger
from douban.douban import DoubanMovieCrawler
from radarr.radarr import Radarr
from sonarr.sonarr import Sonarr
from utils.movie_utils import format_series_title


class MovieBot:
    def __init__(self, **kwargs):
        self.workdir = kwargs['workdir']
        self.douban_config = kwargs['douban']
        self.douban_movie_crawler = DoubanMovieCrawler(self.douban_config['cookies'])
        self.radarr= Radarr(
            host=kwargs['radarr']['host'],
            port=kwargs['radarr']['port'],
            url_base=kwargs['radarr']['url_base'],
            api_key=kwargs['radarr']['api_key'],
            is_https=kwargs['radarr']['https'],
            rootFolderPath=  kwargs['radarr']['rootFolderPath'],
            qualityProfileId= kwargs['radarr']['qualityProfileId'],
            addOptions = kwargs['radarr']['addOptions'],
            minimumAvailability = kwargs['radarr']['minimumAvailability'],
            monitored = kwargs['radarr']['monitored']
        )
        self.sonarr = Sonarr( 
            host=kwargs['sonarr']['host'],
            port=kwargs['sonarr']['port'],
            api_key=kwargs['sonarr']['api_key'],
            is_https=kwargs['sonarr']['https'],
            rootFolderPath=  kwargs['sonarr']['rootFolderPath'],
            qualityProfileId= kwargs['sonarr']['qualityProfileId'],
            languageProfileId = kwargs['sonarr']['languageProfileId'],
            seriesType = kwargs['sonarr']['seriesType'],
            seasonFolder = kwargs['sonarr']['seasonFolder'],
            monitored = kwargs['sonarr']['monitored'],
            addOptions = kwargs['sonarr']['addOptions'],
            genreMappingPath = kwargs['sonarr']['genreMappingPath'],
        )
    def start(self):
        logger.info('开始寻找电影并自动添加，现在时间是 {}', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        users = self.douban_config['user_domain']
        for u in users:
            if u != '':
                self.search_and_add(
                    u,
                    types=self.douban_config['types'],
                    within_days=self.douban_config['within_days'],
                    turn_page=self.douban_config['turn_page'],
                    mode=self.douban_config['mode'],
                    save_fetched_list=self.douban_config['save_fetched_list'],
                    saved_fetched_list=self.douban_config['saved_fetched_list'],
                )
        logger.info('所有用户的影视添加已经完成')


    def search_and_add(self, douban_user, types=['wish'], within_days=365, turn_page=True, mode='fetch_and_add', save_fetched_list=True, saved_fetched_list=''):
        movie_details_list = []
        if mode == 'add_from_file':
            with open(saved_fetched_list, 'r', encoding='utf-8') as file:
                movie_details_list = json.load(file)
        else:
            user_movie_list = self.douban_movie_crawler.get_user_movie_list(douban_user, types=types, within_days=within_days,
                                                     turn_page=turn_page)
            if user_movie_list is None:
                logger.info('{}没有任何影视资源需要添加', douban_user)
                return None
            logger.info('已经获得{}的全部影视，共有{}个需要检索', douban_user, len(user_movie_list))

            for user_movie in user_movie_list:
                movie_details = self.douban_movie_crawler.get_movie_details_by_id(user_movie['imdb_id'])
                if movie_details is None:
                    logger.warning('信息获取异常: {}(imdb_id: {})', user_movie['title'], user_movie['imdb_id'])
                    continue
                logger.info('The details of 《{}》 (original_title: {}, imdb_id: {}) has been fetched', user_movie['title'], user_movie['original_title'], user_movie['imdb_id'])
                movie_details_list.append(movie_details)

        if mode != 'add_from_file' and save_fetched_list:
            file_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + '_fetched_list.json'
            logger.info('Saving the fetched list to {}', file_name)
            with open(file_name, 'w', encoding='utf-8') as fetched_list_file:
                json_obj = json.dumps(movie_details_list, indent = 4, sort_keys = True)
                fetched_list_file.write(json_obj)
            
        if mode != 'fetch_only':
            for movie_details in movie_details_list:
                    self.add_movie(movie_details)

    def add_movie(self, movie_details):
        type = movie_details['type']
        imdb_id = movie_details['imdb_id'].strip()
        title = movie_details['title']
        original_title = movie_details['original_title']
        aliases = movie_details['aliases']
        is_series = 'Series' == type
        if is_series:
           extended_original_titles = [title, original_title]
           extended_original_titles.extend(aliases)
           if self.sonarr.does_series_exist(imdb_id, extended_original_titles):
                logger.info('剧集{}已经存在，跳过添加', title)
           else:
                logger.info('尝试添加剧集《{}》', title)
                formatted_titles = []
                for extended_original_title in extended_original_titles:
                    formatted_titles.append(format_series_title(extended_original_title)) 
                formatted_titles = list(set(formatted_titles))
                self.sonarr.search_series_and_add(movie_details, formatted_titles, extended_original_titles)
        else:
           if self.radarr.does_movie_exist(imdb_id):
                logger.info('电影《{}》已经存在，跳过添加', title)
           else:
                logger.info('尝试添加电影《{}》', title)
                self.radarr.search_movie_and_add(title, imdb_id)
