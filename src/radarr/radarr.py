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

    def search_and_add(self, caller_object_details, list_type):
        imdb_id = caller_object_details["imdb_id"]
        title = caller_object_details["title"]
        if imdb_id is not None:
            imdb_id = imdb_id.strip()
            if self.try_to_add_by_term(
                "imdb:" + imdb_id, caller_object_details, list_type
            ):
                logger.info(
                    "Successfully added《{}》by searching with IMDB ID {}.",
                    title,
                    imdb_id,
                )
                return True
        logger.warning(
            "Unable to find《{}》on IMDB, the movie won't be added to Radarr. You may consider adding it to IMDB first.",
            title,
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
