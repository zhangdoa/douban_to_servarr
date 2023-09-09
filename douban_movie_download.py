import argparse
import datetime
import os
import sys
from src.movie.downloader import Downloader
import yaml

user_setting_name = 'user_config.yml'


def load_user_config(workdir):
    user_setting_filepath = workdir + os.sep + user_setting_name
    with open(user_setting_filepath, 'r', encoding='utf-8') as file:
        user_config = yaml.safe_load(file)
    return user_config


def build_downloader(user_config, workdir):
    if user_config['douban'].get('within_days'):
        within_days = user_config['douban']['within_days']
    else:
        from_date = user_config['douban']['from_date']
        to_date = user_config['douban']['to_date']
        if from_date == 'today':
            from_date = datetime.date.today()
        within_days = (from_date - to_date).days

    saved_fetched_list = ''
    mode = user_config['douban']['mode']
    if mode == 'add_from_file':
        saved_fetched_list = user_config['douban']['saved_fetched_list']
        if not saved_fetched_list or saved_fetched_list == '':
            print("%s mode is specified by the saved fetched list is not set" % (mode))
            return
        
    params = {
        'workdir': workdir,
        'douban': {
            'cookies': user_config['douban']['cookies'],
            'user_domain': user_config['douban']['user_domain'].split(';'),
            'within_days': within_days,
            'turn_page': user_config['douban']['turn_page'],
            'types': user_config['douban']['types'].split(';'),
            'save_fetched_list': user_config['douban']['save_fetched_list'],
            'mode' : user_config['douban']['mode'],
            'saved_fetched_list': saved_fetched_list
        },
        'radarr' : {
            'host': user_config['radarr']['host'],
            'port': user_config['radarr']['port'],
            'api_key': user_config['radarr']['api_key'],
            'https': user_config['radarr']['https'],
            'rootFolderPath':  user_config['radarr']['rootFolderPath'],
            'qualityProfileId': user_config['radarr']['qualityProfileId'],
            'addOptions' : user_config['radarr']['addOptions'],
            'minimumAvailability' : user_config['radarr']['minimumAvailability'],
            'monitored':  user_config['radarr']['monitored'],
        },
        'sonarr' : {
            'host': user_config['sonarr']['host'],
            'port': user_config['sonarr']['port'],
            'api_key': user_config['sonarr']['api_key'],
            'https': user_config['sonarr']['https'],
            'rootFolderPath':  user_config['sonarr']['rootFolderPath'],
            'qualityProfileId': user_config['sonarr']['qualityProfileId'],
            'languageProfileId' : user_config['sonarr']['languageProfileId'],
            'seriesType' : user_config['sonarr']['seriesType'],
            'seasonFolder' : user_config['sonarr']['seasonFolder'] ,
            'monitored': user_config['sonarr']['monitored'],
            'addOptions' : user_config['sonarr']['addOptions'],
            'typeMappingPath': user_config['sonarr']['typeMappingPath'],
        }
    }
    return Downloader(**params)


if __name__ == '__main__':
     # 运行在docker上的时候，workdir = '/data',记得修改, 本地运行 workdir = os.getcwd()
    workdir = os.getcwd()
    if not os.path.exists(workdir):
        print('请提供正确的配置，工作目录不存在：%s' % workdir)
        sys.exit()
    config = load_user_config(workdir)
    downloader = build_downloader(config, workdir)
    if downloader:
        downloader.start()
    else:
        print('Something isn\'t correct, please check the console output for the details')
