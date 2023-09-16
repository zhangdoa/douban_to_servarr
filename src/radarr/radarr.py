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
