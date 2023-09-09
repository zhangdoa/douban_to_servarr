import datetime
import json
from src.movie.douban import DoubanMovieCrawler
from src.radarr.utils import Radarr
from src.sonarr.utils import Sonarr
from src.utils.movie_utils import format_serial_name


class Downloader:
    def __init__(self, **kwargs):
        self.workdir = kwargs['workdir']
        self.douban_config = kwargs['douban']
        self.doubanMovieCrawler = DoubanMovieCrawler(self.douban_config['cookies'])
        self.radarr= Radarr(
            host=kwargs['radarr']['host'],
            port=kwargs['radarr']['port'],
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
            typeMappingPath = kwargs['sonarr']['typeMappingPath'],
        )
    def start(self):
        print('开始寻找电影并自动找种下载，现在时间是 %s' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        users = self.douban_config['user_domain']
        for u in users:
            if u != '':
                self.search_and_download(
                    u,
                    types=self.douban_config['types'],
                    within_days=self.douban_config['within_days'],
                    turn_page=self.douban_config['turn_page'],
                    mode=self.douban_config['mode'],
                    save_fetched_list=self.douban_config['save_fetched_list'],
                    saved_fetched_list=self.douban_config['saved_fetched_list'],
                )
        print('所有用户的影视下载已经完成。')


    def search_and_download(self, douban_user, types=['wish'], within_days=365, turn_page=True, mode='fetch_and_add', save_fetched_list=True, saved_fetched_list=''):
        movie_details_list = []
        if mode == 'add_from_file':
            with open(saved_fetched_list, 'r', encoding='utf-8') as file:
                movie_details_list = json.load(file)
        else:
            user_movie_list = self.doubanMovieCrawler.get_user_movie_list(douban_user, types=types, within_days=within_days,
                                                     turn_page=turn_page)
            if user_movie_list is None:
                print('%s没有任何影视资源需要下载' % douban_user)
                return None
            print('已经获得%s的全部影视，共有%s个需要智能检索' % (douban_user, len(user_movie_list)))

            for user_movie in user_movie_list:
                movie_details = self.doubanMovieCrawler.get_movie_by_id(user_movie['id'])
                if movie_details is None:
                    print('%s(id:%s)信息获取异常' % (user_movie['name'], user_movie['id']))
                    continue
                print('The details of %s(id:%s) has been fetched' % (user_movie['name'], user_movie['id']))
                movie_details_list.append(movie_details)

        if mode != 'add_from_file' and save_fetched_list:
            file_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + '_fetched_list.json'
            print('Saving the fetched list to %s' % (file_name))
            with open(file_name, 'w', encoding='utf-8') as fetched_list_file:
                json_obj = json.dumps(movie_details_list, indent = 4, sort_keys = True)
                fetched_list_file.write(json_obj)
            
        if mode != 'fetch_only':
            for movie_details in movie_details_list:
                    self.add_movie(movie_details)

    def add_movie(self, movie_details):
        type = movie_details['type']
        imdb = movie_details['IMDB'].strip()
        local_name = movie_details['local_name']
        alias = movie_details['alias']
        search_name = movie_details['name']
        is_series = 'Series' == type
        if is_series:
           original_all_name = [search_name, local_name]
           original_all_name.extend(alias)
           format_all_name = []
           for name in original_all_name:
               format_all_name.append(format_serial_name(name)) 
           format_all_name = list(set(format_all_name))
           exist = self.sonarr.exist_serial(imdb, original_all_name)
           if exist:
               print('剧集%s已经存在，跳过下载' %(search_name))
           else:
                print('尝试添加%s' %(search_name))
                self.sonarr.search_not_exist_serial_and_download(movie_details, format_all_name, original_all_name)
        else:
           exist = self.radarr.exist_movie(imdb)
           if exist:
               print('电影%s已经存在，跳过下载' %(search_name))
           else:
                print('尝试添加%s' %(search_name))
                self.radarr.search_not_exist_movie_and_download(search_name, imdb)
