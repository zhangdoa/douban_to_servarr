import json

from loguru import logger
from lxml import etree
from lxml import html

from servarr.servarr import Servarr


class Sonarr(Servarr):
    def __init__(
        self,
        host=None,
        port=None,
        url_base=None,
        api_key=None,
        is_https=False,
        rootFolderPath="/tv",
        monitored=True,
        addOptions={},
        qualityProfileId=1,
        languageProfileId=2,
        seriesType="Standard",
        addSeasonSubfolder=True,
        genreSubfolderPath=[],
    ):
        Servarr.__init__(
            self,
            "series",
            "v3",
            host,
            port,
            url_base,
            api_key,
            is_https,
            rootFolderPath,
            monitored,
            addOptions,
            qualityProfileId,
        )
        self.languageProfileId = languageProfileId
        self.seriesType = seriesType
        self.addSeasonSubfolder = addSeasonSubfolder
        self.genreSubfolderPath = genreSubfolderPath

    def try_to_create_tags(self):
        self.try_to_create_tag("unwatched")
        self.try_to_create_tag("watching")
        self.try_to_create_tag("watched")

    def remove_old_tags(self, servarr_object_info):
        self.remove_old_tag(servarr_object_info, "unwatched")
        self.remove_old_tag(servarr_object_info, "watching")
        self.remove_old_tag(servarr_object_info, "watched")

    def list_type_to_tag_label(self, list_type):
        if list_type == "wish":
            return "unwatched"
        if list_type == "do":
            return "watching"
        if list_type == "collect":
            return "watched"
        return None

    def get_apply_tags_data(self, servarr_object_info, found_added_tag_id):
        data = {}
        data["movieIds"] = []
        data["movieIds"].append(servarr_object_info["id"])
        data["tags"] = []
        data["tags"].append(found_added_tag_id)
        return data

    def is_any_matching(self, external_id, searching_titles, item):
        is_external_id_matching = "imdbId" in item and item["imdbId"] == external_id
        is_title_matching = "title" in item and item["title"] in searching_titles
        return is_external_id_matching or is_title_matching

    # TODO: Sonarr's search engine is based on TVDB which can't always return a good result with an IMDB-originated metadata. It needs to be improved by Sonarr's developers
    def search_and_add(self, caller_object_details, list_type):
        external_id = caller_object_details["external_id"]
        if external_id is None:
            return None

        # TODO: Better move this to an earlier stage so we won't be spammed by the different seasons
        # Try to get the series IMDB ID from the title's page, assuming it's a multi-season series and the external_id provided is the episode's ID
        imdb_url = "https://www.imdb.com/title/%s" % external_id
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }
        imdb_res = self.request_wrapper.get(imdb_url, headers=headers)
        imdb_episode_page = etree.HTML(imdb_res.text)
        found_series_imdb_url = imdb_episode_page.xpath(
            '//span[text()="All episodes"]/parent::a/@href'
        )

        # We're not on the only season page of the series, which means the IMDB ID needs to be replaced
        if len(found_series_imdb_url) > 0:
            external_id = found_series_imdb_url[0]
            first_substring = "/title/"
            end_substring = "/episodes/"
            external_id = external_id[
                external_id.find(first_substring)
                + len(first_substring) : external_id.find(end_substring)
            ]

        # Then get the TVDB ID
        tvdb_url = (
            "https://thetvdb.com/api/GetSeriesByRemoteID.php?imdbid=%s" % external_id
        )
        tvdb_res = self.request_wrapper.get(tvdb_url, headers=headers)
        tvdb_html = html.fromstring(bytes(tvdb_res.text, encoding="utf8"))
        tvdb_ids = tvdb_html.xpath("//seriesid/text()")

        titles = caller_object_details["titles"]
        if tvdb_ids is not None and len(tvdb_ids) > 0:
            tvdb_id = tvdb_ids[0]
            # To prevent false positives from the matching checker
            caller_object_details["external_id"] = external_id
            if self.try_to_add_by_term(
                "tvdb:" + tvdb_id, caller_object_details, list_type
            ):
                logger.info(
                    'Successfully added "{}" by searching with TVDB ID {}.',
                    titles,
                    tvdb_id,
                )
                return True
            else:
                return False

        logger.warning(
            'Unable to find "{}" on TVDB, the series won\'t be added to Sonarr. You may consider adding it to TVDB first.',
            titles,
        )
        return None

    def get_add_call_params(
        self, caller_object_details, servarr_object_info, list_type
    ):
        params = Servarr.get_add_call_params(
            self, caller_object_details, servarr_object_info, list_type
        )
        params["languageProfileId"] = self.languageProfileId
        params["seriesType"] = self.seriesType
        params["addSeasonSubfolder"] = self.addSeasonSubfolder
        genres = caller_object_details["genres"]
        if genres is not None and len(genres) > 0:
            for genre in genres:
                for t in self.genreSubfolderPath:
                    if genre in t["genre"]:
                        params["rootFolderPath"] = self.rootFolderPath + t["path"]
                        params["seriesType"] = t["seriesType"]
        return params
