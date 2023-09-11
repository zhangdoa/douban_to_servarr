import datetime
import random
import time

import requests
import urllib3


class RequestUtils:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    __last_request_time = None

    def __init__(
        self,
        request_interval_mode=False,
        max_attempt=6,
        min_request_interval_in_ms=1000,
        max_request_interval_in_ms=5000,
        min_sleep_secs=1.0,
        max_sleep_secs=10.0,
    ):
        self.request_interval_mode = request_interval_mode
        self.session = requests.Session()
        self.max_attempt = max_attempt
        self.min_request_interval_in_ms = min_request_interval_in_ms
        self.max_request_interval_in_ms = max_request_interval_in_ms
        self.min_sleep_secs = min_sleep_secs
        self.max_sleep_secs = max_sleep_secs

    def check_request(self):
        if not self.request_interval_mode:
            return
        if self.__last_request_time is None:
            self.__last_request_time = datetime.datetime.now()
            return
        time_since_last_request = datetime.datetime.now() - self.__last_request_time
        time_since_last_request_ms = time_since_last_request.microseconds / 1000
        if time_since_last_request_ms < random.randint(
            self.min_request_interval_in_ms, self.max_request_interval_in_ms
        ):
            min_sleep_secs = self.min_sleep_secs
            max_sleep_secs = self.max_sleep_secs - (time_since_last_request_ms / 1000)
            if max_sleep_secs <= min_sleep_secs:
                max_sleep_secs = min_sleep_secs * 2
            sleep_secs = random.uniform(self.min_sleep_secs, self.max_sleep_secs)
            time.sleep(sleep_secs)
        self.__last_request_time = datetime.datetime.now()

    def post_and_return_content(self, url, params, headers={}):
        i = 0
        while i < self.max_attempt:
            try:
                self.check_request()
                r = self.session.post(url, data=params, verify=False, headers=headers)
                return str(r.content, "UTF-8")
            except self.session.exceptions.RequestException:
                i += 1

    def get_and_return_content(self, url, params=None, headers=None):
        i = 0
        while i < self.max_attempt:
            try:
                self.check_request()
                r = self.session.get(url, verify=False, headers=headers, params=params)
                return str(r.content, "UTF-8")
            except requests.exceptions.RequestException:
                i += 1

    def get(self, url, params=None, headers={}):
        i = 0
        while i < self.max_attempt:
            try:
                self.check_request()
                return self.session.get(
                    url, params=params, verify=False, headers=headers
                )
            except requests.exceptions.RequestException as e:
                print(e)
                i += 1

    def post(self, url, params=None, data=None, headers={}, allow_redirects=True):
        i = 0
        while i < self.max_attempt:
            try:
                self.check_request()
                return self.session.post(
                    url,
                    data=data,
                    params=params,
                    verify=False,
                    headers=headers,
                    allow_redirects=allow_redirects,
                )
            except requests.exceptions.RequestException as e:
                print(e)
                i += 1

    def put(self, url, data=None, headers={}, allow_redirects=True):
        i = 0
        while i < self.max_attempt:
            try:
                self.check_request()
                return self.session.put(
                    url,
                    data=data,
                    verify=False,
                    headers=headers,
                    allow_redirects=allow_redirects,
                )
            except requests.exceptions.RequestException as e:
                print(e)
                i += 1
