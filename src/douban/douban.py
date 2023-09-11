import datetime
import html
import re

import cn2an
from lxml import etree
from loguru import logger

from utils.http_utils import RequestUtils


class DoubanMovieCrawler:
    def __init__(self, cookies):
        self.__headers = {
            "Referer": "https://movie.douban.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }
        self.req = RequestUtils(request_interval_mode=True)
        # 先访问一次首页，显得像个正常人
        initial_headers = self.__headers
        initial_headers["Cookies"] = cookies
        res = self.request_get("https://movie.douban.com/", headers=initial_headers)

    def atoi(self, str):
        if str.isdigit():
            return int(str)
        else:
            return cn2an.cn2an(str)

    def request_get(self, url, headers):
        res = self.req.get(url=url, headers=headers)
        if res == None:
            logger.error("Bad result returned when requesting {}", url)
            return None
        text = res.text
        if text.find("有异常请求从你的 IP 发出") != -1:
            logger.warning(
                "The crawler is detected, please try again with a different IP"
            )
            return None
        return res

    def get_movie_details(self, url):
        res = self.request_get(url, headers=self.__headers)
        if res == None:
            return None

        text = res.text
        # mandatory fields
        found_titles = re.findall('<span property="v:itemreviewed">(.+)</span>', text)
        if len(found_titles) > 0:
            title = found_titles[0]
        else:
            logger.error("Can't find any titles for {}", url)
            return None

        found_imdb_ids = re.findall('<span class="pl">IMDb: </span>([^<]+)<br>', text)
        imdb_id = ""
        if len(found_imdb_ids) > 0:
            imdb_id = found_imdb_ids[0]

        # less critical fields(?)
        found_aliases = re.findall('<span class="pl">又名:</span>([^<]+)<br/>', text)
        aliases = []
        if len(found_aliases) > 0:
            aliases = found_aliases[0].strip().split(" / ")
        aliases = list(map(lambda x: html.unescape(x), aliases))

        found_years = re.findall(r'<span class="year">\((\d+)\)</span>', text)
        if len(found_years) > 0:
            year = found_years[0]

        found_genres = re.findall(r'<span\s+property="v:genre">([^>]+)</span>', text)
        genres = []
        for genre in found_genres:
            genres.append(genre)

        found_release_dates = re.findall(
            r'<span property="v:initialReleaseDate" content="(\d+-\d+-\d+)\(([^)]+)\)">',
            text,
        )
        release_dates = []
        found_release_dates.sort(reverse=False)
        for release_date in found_release_dates:
            release_dates.append({"date": release_date[0], "region": release_date[1]})

        found_seasons = re.search(r'<span\s*class="pl">季数:</span>\s*(\d+)<br/>', text)
        seasons = None
        if found_seasons:
            seasons = found_seasons.group(1)

        found_episodes = re.findall(r'<span class="pl">集数:</span>\s*(\d+)<br/>', text)
        if found_episodes is not None and len(found_episodes) > 0:
            episodes = int(str(found_episodes[0]))
            type = "Series"
            # 当影视为剧集时，本地语言影视名，需要考虑到第*季字符的影响，不能直接按空格切分，如 权力的游戏 第八季 Game。。。
            found_seasons = re.search("第(.+)季", title)
            if found_seasons:
                season_str_in_title = found_seasons.group()
                if seasons is None:
                    seasons = self.atoi(found_seasons.group(1))
                first_space_idx = title.find(season_str_in_title + " ")
                if first_space_idx != -1:
                    first_space_idx = first_space_idx + len(season_str_in_title)
            else:
                first_space_idx = title.find(" ")
                seasons = 1
            original_title = title[first_space_idx + 1 : len(title)]
        else:
            type = "Movie"
            episodes = 1
            first_space_idx = title.find(" ")
            original_title = title[first_space_idx + 1 : len(title)]
        if first_space_idx != -1:
            title = title[0:first_space_idx]
        return {
            "type": type,
            "title": html.unescape(title),
            "original_title": html.unescape(original_title),
            "aliases": aliases,
            "year": year,
            "genres": genres,
            "release_dates": release_dates,
            "imdb_id": imdb_id,
            "seasons": seasons,
            "episodes": episodes,
        }

    def get_movie_details_by_id(self, id):
        return self.get_movie_details("https://movie.douban.com/subject/%s" % id)

    def get_user_movie_lists(
        self, user, list_types=["wish"], within_days=365, turn_page=True
    ) -> object:
        """
        获取豆瓣电影想看
        :param user: 豆瓣唯一账号
        :param types: 豆瓣用户电影类型，支持wish（想看）、do（在看）、collect（看过）
        :param within_days:多少天内加入想看的影视，默认365
        :param turn_page: 是否自动翻页
        :return: {'title': '地球改变之年'
        , 'original_title': 'The Year Earth Changed'
        , 'year': '2021'
        , 'type': 'Movie'
        , 'count': None
        , 'release_date': [{'date': '2021-04-16', 'region': '美国'}]
        , 'genre': ['纪录片']
        , 'added_date': '2022-01-01'}
        """
        movie_lists = {}
        for type in list_types:
            logger.info("开始获取{} {}的影视", user, type)
            offset = 0
            uri = "/people/%s/%s?start=%s&sort=time&rating=all&filter=all&mode=grid" % (
                user,
                type,
                offset,
            )
            page_count = 1
            movie_list = []
            while uri is not None:
                url = "https://movie.douban.com" + uri
                res = self.request_get(url, headers=self.__headers)
                if res == None:
                    return None
                html = etree.HTML(res.text)
                page = html.xpath('//div[@class="paginator"]/span[@class="next"]/a')
                if len(page) > 0:
                    uri = page[0].attrib["href"]
                else:
                    uri = None
                movie_list_url = html.xpath('//li[@class="title"]/a/@href')
                added_date_list = html.xpath('//li/span[@class="date"]/text()')
                movie_list_a = html.xpath('//li[@class="title"]/a/em/text()')
                for i in range(len(movie_list_a)):
                    added_date = added_date_list[i]
                    days = (
                        datetime.datetime.now()
                        - datetime.datetime.strptime(added_date, "%Y-%m-%d")
                    ).days
                    if within_days is not None and days > within_days:
                        turn_page = False
                        continue
                    url = movie_list_url[i]
                    titles = movie_list_a[i].split(" / ")
                    if len(titles) > 1:
                        original_title = titles[1]
                    else:
                        original_title = None
                    found_ids = re.search(r"/subject/(\d+)", url)
                    if found_ids:
                        id = found_ids.group(1)
                    else:
                        id = None
                    movie_list.append(
                        {
                            "id": id.strip(),
                            "title": titles[0],
                            "original_title": original_title,
                            "url": url,
                            "added_date": added_date,
                        }
                    )
                if not turn_page:
                    break
                if uri is not None:
                    logger.info("已经完成{}页数据的获取，开始获取下一页...", page_count)
                    page_count = page_count + 1
            movie_lists[type] = movie_list
            logger.info("{}天之内加入{}的影视，共{}部", within_days, type, len(movie_list))
        return movie_lists
