import json

from loguru import logger

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

    def add(self, caller_object_details, servarr_object_info, list_type):
        api = "/api/v3/series"
        params = self.get_add_call_params(servarr_object_info, list_type)
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

        r = self.request_wrapper.post(
            self.server + api, data=json.dumps(params), headers=self.headers
        )
        content = json.loads(str(r.content, "UTF-8"))
        if r.status_code == 201:
            logger.info('Successfully added: "{}"', (servarr_object_info["title"]))
        elif content["errorCode"] == "EqualValidator":
            logger.info(
                '"{}" should have been added with a different season.',
                (servarr_object_info["title"]),
            )
        else:
            logger.error('Failed to add: "{}"', (servarr_object_info["title"]))
