import json

from loguru import logger
from lxml import etree
from lxml import html

from servarr.servarr import Servarr


class Lidarr(Servarr):
    def __init__(
        self,
        host=None,
        port=None,
        url_base=None,
        api_key=None,
        is_https=False,
        rootFolderPath="/music",
        monitored=True,
        addOptions={},
        qualityProfileId=1,
        metadataProfileId=1,
    ):
        Servarr.__init__(
            self,
            "album",
            "v1",
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

        self.metadataProfileId = metadataProfileId

    def is_any_matching(self, external_id, searching_titles, item):
        title_lowercase = item["title"].lower()
        for searching_title in searching_titles:
            if searching_title.lower() == title_lowercase:
                return True
        return False

    def try_to_search_with_mb_url(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }
        mb_res = self.request_wrapper.get(url, headers=headers)
        mb_html = html.fromstring(bytes(mb_res.text, encoding="utf8"))
        return mb_html.xpath("//release[1]/release-group[1]/@id")

    def try_to_search_with_all_possible_terms(self, caller_object_details):
        external_id = caller_object_details["external_id"]
        found_release_group_urls = []
        if external_id is not None:
            mb_url = (
                "https://musicbrainz.org/ws/2/release/?query=barcode:%s" % external_id
            )
            found_release_group_urls = self.try_to_search_with_mb_url(mb_url)
            if len(found_release_group_urls) > 0:
                return found_release_group_urls

        titles = caller_object_details["titles"]
        for title in titles:
            mb_url = "https://musicbrainz.org/ws/2/release/?query=release:%s" % title
            found_release_group_urls = self.try_to_search_with_mb_url(mb_url)
            if len(found_release_group_urls) > 0:
                return found_release_group_urls

        return found_release_group_urls

    def search_and_add(self, caller_object_details, list_type):
        external_id = caller_object_details["external_id"]
        found_release_group_urls = self.try_to_search_with_all_possible_terms(
            caller_object_details
        )

        mb_id = ""
        if len(found_release_group_urls) > 0:
            mb_id = str(found_release_group_urls[0])

        titles = caller_object_details["titles"]
        if len(mb_id) > 0:
            mb_id = mb_id.strip()
            if self.try_to_add_by_term(
                "lidarr:" + mb_id, caller_object_details, list_type
            ):
                logger.info(
                    'Successfully added "{}" by searching with MusicBrainz ID {}.',
                    titles,
                    mb_id,
                )
                return True
        logger.warning(
            'Unable to find "{}" with barcode {} on MusicBrainz, the album won\'t be added to Lidarr. You may consider adding it to MusicBrainz first.',
            titles,
            external_id,
        )
        return None

    def get_add_call_params(
        self, caller_object_details, servarr_object_info, list_type
    ):
        params = servarr_object_info
        params["profileId"] = self.qualityProfileId
        params["monitored"] = self.monitored
        params["artist"]["qualityProfileId"] = self.qualityProfileId
        params["artist"]["metadataProfileId"] = self.metadataProfileId
        params["artist"]["rootFolderPath"] = self.rootFolderPath
        params["artist"]["monitored"] = self.monitored
        params["addOptions"] = self.addOptions
        self.try_to_set_tags(params, list_type)
        return params
