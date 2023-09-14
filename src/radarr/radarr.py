import json

from loguru import logger

from servarr.servarr import Servarr


class Radarr(Servarr):
    def __init__(
        self,
        host=None,
        port=None,
        url_base=None,
        api_key=None,
        is_https=False,
        rootFolderPath="/movie",
        monitored=True,
        addOptions={},
        qualityProfileId=1,
        minimumAvailability="",
    ):
        Servarr.__init__(
            self,
            "movie",
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
        self.minimumAvailability = minimumAvailability

    def is_any_matching(self, external_id, searching_titles, item):
        is_external_id_matching = "imdbId" in item and item["imdbId"] == external_id
        is_title_matching = "title" in item and item["title"] in searching_titles
        return is_external_id_matching or is_title_matching

    def search_and_add(self, caller_object_details, list_type):
        external_id = caller_object_details["external_id"]
        titles = caller_object_details["titles"]
        if external_id is not None:
            external_id = external_id.strip()
            if self.try_to_add_by_term(
                "imdb:" + external_id, caller_object_details, list_type
            ):
                logger.info(
                    'Successfully added "{}" by searching with IMDB ID {}.',
                    titles,
                    external_id,
                )
                return True
        logger.warning(
            'Unable to find "{}" on IMDB, the movie won\'t be added to Radarr. You may consider adding it to IMDB first.',
            titles,
        )
        return None

    def get_add_call_params(
        self, caller_object_details, servarr_object_info, list_type
    ):
        params = Servarr.get_add_call_params(
            self, caller_object_details, servarr_object_info, list_type
        )
        params["minimumAvailability"] = self.minimumAvailability
        return params
