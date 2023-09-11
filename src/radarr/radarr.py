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

    def add(self, caller_object_details, servarr_object_info, list_type):
        api = "/api/v3/movie"
        params = self.get_add_call_params(servarr_object_info, list_type)
        params["minimumAvailability"] = self.minimumAvailability

        r = self.request_wrapper.post(
            self.server + api, params=json.dumps(params), headers=self.headers
        )
        if r.status == 200:
            logger.info('Successfully added: "{}".', (servarr_object_info["title"]))
        else:
            logger.error('Failed to add: "{}".', (servarr_object_info["title"]))
