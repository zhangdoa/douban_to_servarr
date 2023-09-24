import datetime
import html
import re

import cn2an
from lxml import etree
from loguru import logger
from bs4 import BeautifulSoup

from utils.request_utils import RequestUtils


class DoubanCrawler:
    def __init__(self, category, cookies):
        self.category = category
        self.url = "https://%s.douban.com" % self.category
        self.headers = {
            "Referer": self.url,
            "Accept-Encoding": "gzip",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }
        self.request_wrapper = RequestUtils(request_interval_mode=True)

        # Initialize the session
        initial_headers = self.headers
        if cookies != "":
            initial_headers["Cookies"] = cookies
        res = self.request_get(self.url, headers=initial_headers)
        if res is None or res.status_code != 200:
            logger.error("Failed to create a crawler for category {}.", self.category)

    def atoi(self, str):
        if str.isdigit():
            return int(str)
        else:
            return cn2an.cn2an(str)

    def request_get(self, url, headers):
        res = self.request_wrapper.get(url=url, headers=headers)
        if res == None:
            logger.error("Bad result returned when requesting {}.", url)
            return None
        if res.status_code != 200:
            logger.warning("Unable to scrape {}.", url)
            return None
        return res

    def get_user_entry_lists(
        self, user, list_types, start_date, end_date, start_page
    ) -> object:
        entry_lists = {}
        for list_type in list_types:
            logger.info(
                'Start to scrape list "{}" for {} on {}, from {} to {}.',
                list_type,
                user,
                self.url,
                start_date,
                end_date,
            )
            offset = (start_page - 1) * 15
            uri = "/people/%s/%s?start=%s&sort=time&rating=all&filter=all&mode=grid" % (
                user,
                list_type,
                offset,
            )
            page_count = 1
            entry_list = []
            turn_page = True
            while uri is not None:
                # The next page href is not consistent on different category's pages
                if self.url in uri:
                    url = uri
                else:
                    url = self.url + uri
                res = self.request_get(url, headers=self.headers)
                if res == None:
                    continue
                html = etree.HTML(res.text)
                page = html.xpath('//div[@class="paginator"]/span[@class="next"]/a')
                if len(page) > 0:
                    uri = page[0].attrib["href"]
                else:
                    uri = None
                entry_list_url = html.xpath('//li[@class="title"]/a[1]/@href')
                added_date_list = html.xpath('//li/span[@class="date"]/text()')
                entry_list_a = html.xpath('//li[@class="title"]/a/em')
                for i in range(len(entry_list_a)):
                    added_date_str = added_date_list[i]
                    added_date = datetime.datetime.strptime(
                        added_date_str, "%Y-%m-%d"
                    ).date()
                    if added_date > start_date:
                        continue
                    if added_date < end_date:
                        turn_page = False
                        continue
                    url = entry_list_url[i]
                    titles = entry_list_a[i].text.split(" / ")
                    if entry_list_a[i].tail is not None:
                        alternative_titles = entry_list_a[i].tail.strip().split(" / ")
                        if (
                            alternative_titles is not None
                            and len(alternative_titles) > 0
                        ):
                            # Remove "/ "
                            alternative_titles[0] = alternative_titles[0][
                                2 : len(alternative_titles[0])
                            ]
                            titles.extend(alternative_titles)
                    found_ids = re.search(r"/subject/(\d+)", url)
                    if found_ids:
                        id = found_ids.group(1)
                    else:
                        id = None
                    entry_list.append(
                        {
                            "id": id.strip(),
                            "titles": titles,
                            "url": url,
                            "added_date": added_date_str,
                        }
                    )
                if not turn_page:
                    break
                if uri is not None:
                    logger.info(
                        "Page {} has been scraped, moving to the next one...",
                        start_page - 1 + page_count,
                    )
                    page_count = page_count + 1
            if len(entry_list) > 0:
                entry_lists[list_type] = entry_list
            logger.info("Total scraped entries: {} on {}.", len(entry_list), self.url)
        return entry_lists

    def get_details_by_id(self, id):
        return self.get_entry_details("%s/subject/%s" % (self.url, id))

    def get_entry_details(self, url):
        return None


class DoubanMovieCrawler(DoubanCrawler):
    def get_entry_details(self, url):
        res = self.request_get(url, headers=self.headers)
        if res == None:
            return None

        text = res.text
        soup = BeautifulSoup(text, "lxml")
        html = etree.HTML(str(soup).strip())

        episode = None
        external_id = ""
        found_info_span_list = html.xpath('//div[@id="info"]/span')
        if len(found_info_span_list) > 0:
            for found_info_span in found_info_span_list:
                if found_info_span.text == "集数:":
                    episode = found_info_span.tail.strip()
                elif found_info_span.text == "IMDb:":
                    external_id = found_info_span.tail.strip()
        else:
            logger.warning('Unable to get the media info for "{}".', url)

        found_genres = html.xpath('//span[@property="v:genre"]')
        genres = []
        for genre in found_genres:
            genres.append(genre.text.strip())

        if episode is not None and episode != "":
            type = "Series"
        else:
            type = "Movie"

        result = {
            "type": type,
            "genres": genres,
            "external_id": external_id,
        }
        logger.info(
            "Scraped: {}.",
            result,
        )
        return result


class DoubanMusicCrawler(DoubanCrawler):
    def get_entry_details(self, url):
        res = self.request_get(url, headers=self.headers)
        if res == None:
            return None

        text = res.text
        soup = BeautifulSoup(text, "lxml")
        html = etree.HTML(str(soup).strip())

        found_titles = html.xpath('//div[@id="wrapper"]/h1/span/text()')
        if len(found_titles) > 0:
            titles = found_titles
        else:
            logger.error("Can't find any titles for {}", url)
            return None

        aliases = []
        release_date = ""
        external_id = ""
        label = ""
        found_info_span_list = html.xpath('//div[@id="info"]/span')
        if len(found_info_span_list) > 0:
            for found_info_span in found_info_span_list:
                if found_info_span.text == "又名:":
                    aliases = found_info_span.tail.strip()
                elif found_info_span.text == "出版者:":
                    label = found_info_span.tail.strip()
                elif found_info_span.text == "发行时间:":
                    release_date = found_info_span.tail.strip()
                elif found_info_span.text == "条形码:":
                    external_id = found_info_span.tail.strip()
        else:
            logger.warning('Unable to get the album info for "{}".', titles)

        artists = []
        found_artists_span_list = html.xpath('//div[@id="info"]/span/span/a')
        if len(found_artists_span_list) > 0:
            for found_artist in found_artists_span_list:
                artists.append(found_artist.text.strip())

        result = {
            "type": "Music",
            "titles": titles,
            "aliases": aliases,
            "artists": artists,
            "label": label,
            "release_date": release_date,
            "external_id": external_id,
        }
        logger.info(
            "Scraped: {}",
            result,
        )
        return result
