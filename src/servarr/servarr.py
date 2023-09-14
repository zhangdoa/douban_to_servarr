import json

from loguru import logger

from utils.http_utils import RequestUtils
from utils.movie_utils import format_series_title


class Servarr:
    def __init__(
        self,
        api_type="",
        api_version="v3",
        host=None,
        port=None,
        url_base=None,
        api_key=None,
        is_https=False,
        rootFolderPath="/",
        monitored=True,
        addOptions={},
        qualityProfileId=1,
    ):
        self.api_type = api_type
        self.api_version = api_version
        self.request_wrapper = RequestUtils(
            request_interval_mode=True,
            max_attempt=6,
            min_request_interval_in_ms=200,
            max_request_interval_in_ms=500,
            min_sleep_secs=0.1,
            max_sleep_secs=0.2,
        )
        self.host = host
        self.port = port
        self.rootFolderPath = rootFolderPath
        self.monitored = monitored
        self.addOptions = addOptions
        self.qualityProfileId = qualityProfileId
        self.headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
        self.server = "%s://%s%s%s" % (
            "https" if is_https else "http",
            host,
            ":" if url_base == "" else "",
            port if url_base == "" else url_base,
        )

        self.tags = self.get_tags()

        self.try_to_create_tag("unwatched")
        self.try_to_create_tag("watching")
        self.try_to_create_tag("watched")
        self.update_tags()

        self.added_items = self.get_added_items()

    def get_tags(self):
        api = "/api/%s/tag" % self.api_version
        r = self.request_wrapper.get_and_return_content(
            self.server + api, headers=self.headers
        )
        if r is not None:
            result = json.loads(r)
            logger.info("Already added tags: {}", result)
            return result
        else:
            logger.warning(
                "Trying to get the added tags but the result is none. The tags won't be updated correctly."
            )
            return None

    def try_to_create_tag(self, label):
        found_tag = self.find_tag_by_label(label, self.tags)
        new_tag = {}
        if found_tag is not None and len(found_tag) == 0:
            new_tag["label"] = label
            new_tag["id"] = len(self.tags) + 1
            self.tags.append(new_tag)
            logger.info('New tag "{}" needs to be added.', label)

    def update_tags(self):
        if self.tags is None:
            return None
        api = "/api/%s/tag" % self.api_version
        for tag in self.tags:
            r = self.request_wrapper.post(
                self.server + api, data=json.dumps(tag), headers=self.headers
            )
            if r is None:
                return None
            # TODO: This would return a 500 and saying "Can't insert model with existing ID x" if the ID x is not added yet...
            if r.status_code != 202 and r.status_code != 201:
                logger.warning('Can\'t added tag "{}"', tag)

    def find_tag_by_label(self, label, tags):
        if tags is not None and len(tags) > 0:
            return list(filter(lambda tag: tag["label"] == label, tags))
        return None

    def try_to_update_watching_status(self, servarr_object_info, list_type):
        new_tag_label = self.list_type_to_tag_label(list_type)
        if new_tag_label is None:
            return None
        found_added_tags = self.find_tag_by_label(new_tag_label, self.tags)
        if found_added_tags is None or len(found_added_tags) == 0:
            return None

        found_added_tag_id = found_added_tags[0]["id"]
        if found_added_tag_id in servarr_object_info["tags"]:
            return False

        self.remove_old_tag(servarr_object_info, "unwatched")
        self.remove_old_tag(servarr_object_info, "watching")
        self.remove_old_tag(servarr_object_info, "watched")

        api = "/api/%s/%s/editor" % (self.api_version, self.api_type)
        data = self.get_apply_tags_data(servarr_object_info, found_added_tag_id)
        data["applyTags"] = "add"
        r = self.request_wrapper.put(
            self.server + api, data=json.dumps(data), headers=self.headers
        )
        if r is None:
            return None
        if r.status_code == 202:
            logger.info(
                'Successfully updated the status tag of {} to "{}".',
                servarr_object_info["titles"],
                found_added_tags[0]["label"],
            )
            return True
        else:
            return None

    def get_apply_tags_data(self, servarr_object_info, found_added_tag_id):
        data = {}
        data["movieIds"] = []
        data["movieIds"].append(servarr_object_info["id"])
        data["tags"] = []
        data["tags"].append(found_added_tag_id)
        return data

    def list_type_to_tag_label(self, list_type):
        if list_type == "wish":
            return "unwatched"
        if list_type == "do":
            return "watching"
        if list_type == "collect":
            return "watched"
        return None

    def remove_old_tag(self, servarr_object_info, old_tag_label):
        found_added_tags = self.find_tag_by_label(old_tag_label, self.tags)
        if found_added_tags is None or len(found_added_tags) == 0:
            return False

        found_added_tag_id = found_added_tags[0]["id"]
        if found_added_tag_id not in servarr_object_info["tags"]:
            return False

        api = "/api/%s/%s/editor" % (self.api_version, self.api_type)
        data = self.get_apply_tags_data(servarr_object_info, found_added_tag_id)
        data["applyTags"] = "remove"
        r = self.request_wrapper.put(
            self.server + api, data=json.dumps(data), headers=self.headers
        )
        if r is None:
            return None
        if r.status_code == 202:
            logger.info(
                'Successfully removed the tag "{}" of {}.',
                old_tag_label,
                servarr_object_info["titles"],
            )
            return True
        else:
            return None

    def get_added_items(self):
        api = "/api/%s/%s" % (self.api_version, self.api_type)
        r = self.request_wrapper.get_and_return_content(
            self.server + api, headers=self.headers
        )
        if r is not None:
            return json.loads(r)
        else:
            logger.warning("Trying to get the added items but the result is none.")
            return None

    def try_to_add_item(self, caller_object_details, list_type):
        titles = caller_object_details["titles"]
        added_item = self.find_added_item(caller_object_details)
        if added_item is not None:
            watching_status_update_result = self.try_to_update_watching_status(
                added_item, list_type
            )
            if watching_status_update_result is not None:
                if watching_status_update_result == False:
                    logger.info(
                        '"{}" has already been added. Skip the process.', titles
                    )
            else:
                logger.warning(
                    'Failed to update the watching status of "{}". There might be server-side issues.',
                    titles,
                )
        else:
            logger.info('Trying to add"{}"...', titles)
            self.search_and_add(caller_object_details, list_type)

    def find_added_item(self, caller_object_details):
        external_id = caller_object_details["external_id"].strip()
        searching_titles = self.get_searching_titles(caller_object_details)
        if self.added_items is not None:
            for item in self.added_items:
                if self.is_any_matching(external_id, searching_titles, item):
                    return item
        return None

    def is_any_matching(self, external_id, searching_titles, item):
        return False

    # Searching-by-titles is generally not as accurate as the ID-based searching. This is an example implementation and shouldn't be used in general.
    def search_and_add(self, caller_object_details, list_type):
        titles = caller_object_details["titles"]
        searching_titles = self.get_searching_titles(caller_object_details)
        for searching_title in searching_titles:
            if self.try_to_add_by_term(
                searching_title, caller_object_details, list_type
            ):
                logger.info(
                    'Successfully added "{}" by searching with the term "{}".',
                    titles,
                    searching_title,
                )
                return True

        logger.warning('Can\'t find "{}".', titles)
        return False

    def get_searching_titles(self, caller_object_details):
        searching_titles = caller_object_details["titles"]
        searching_titles.extend(caller_object_details["aliases"])
        for idx, searching_title in enumerate(searching_titles):
            searching_titles[idx] = format_series_title(searching_title)
        return searching_titles

    def search_item_by_term(self, term):
        api = "/api/%s/%s/lookup" % (self.api_version, self.api_type)
        r = self.request_wrapper.get_and_return_content(
            self.server + api, params={"term": term}, headers=self.headers
        )
        if r is not None:
            return json.loads(r)
        else:
            return None

    def try_to_add_by_term(self, term, caller_object_details, list_type):
        found_items = self.search_item_by_term(term)
        if found_items is not None and len(found_items) > 0:
            external_id = caller_object_details["external_id"]
            searching_titles = self.get_searching_titles(caller_object_details)
            for found_item in found_items:
                if self.is_any_matching(external_id, searching_titles, found_item):
                    return self.add(caller_object_details, found_item, list_type)
        return False

    def add(self, caller_object_details, servarr_object_info, list_type):
        api = "/api/%s/%s" % (self.api_version, self.api_type)
        params = self.get_add_call_params(
            caller_object_details, servarr_object_info, list_type
        )
        r = self.request_wrapper.post(
            self.server + api, data=json.dumps(params), headers=self.headers
        )
        content = json.loads(str(r.content, "UTF-8"))
        if r.status_code == 201:
            return True
        # TODO: Better parse this and filter out the already-added case
        elif len(content) > 0:
            logger.info(
                'Failed to add "{}". The server says: "{}".',
                (caller_object_details["titles"]),
                content,
            )
            return False
        else:
            logger.error('Failed to add: "{}".', (caller_object_details["titles"]))
            return None

    def get_add_call_params(
        self, caller_object_details, servarr_object_info, list_type
    ):
        params = servarr_object_info
        params["qualityProfileId"] = self.qualityProfileId
        params["rootFolderPath"] = self.rootFolderPath
        params["monitored"] = self.monitored
        params["addOptions"] = self.addOptions
        self.try_to_set_tags(params, list_type)
        return params

    def try_to_set_tags(self, params, list_type):
        tag_label = self.list_type_to_tag_label(list_type)
        if tag_label is not None:
            found_added_tags = self.find_tag_by_label(tag_label, self.tags)
            if found_added_tags is not None and len(found_added_tags) > 0:
                params["tags"].append(found_added_tags[0]["id"])
