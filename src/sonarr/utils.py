
import json

from loguru import logger

from src.utils.http_utils import RequestUtils
from src.utils.movie_utils import format_series_title
from src.utils.movie_utils import series_title_match

class Sonarr:
  def __init__(self, host=None, port=None, api_key=None, is_https=False, rootFolderPath="/media/电影",qualityProfileId=1, languageProfileId = 2, seriesType = 'Standard',seasonFolder = True, monitored = True, addOptions = {}, genreMappingPath = [] ):
      self.req = RequestUtils(request_interval_mode=True, max_attempt=6, min_request_interval_in_ms=200, max_request_interval_in_ms=500, min_sleep_secs=0.1, max_sleep_secs=0.2)
      self.host = host
      self.port = port
      self.rootFolderPath = rootFolderPath
      self.qualityProfileId = qualityProfileId
      self.languageProfileId = languageProfileId
      self.seriesType = seriesType
      self.addOptions = addOptions
      self.genreMappingPath = genreMappingPath
      self.seasonFolder = seasonFolder
      self.monitored = monitored
      self.headers={
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
      }
      self.server = '%s://%s:%s' % ("https" if is_https else "http", host, port)

  def get_added_series(self):
    api = '/api/v3/series'
    series_list = self.req.get_and_return_content(self.server + api, headers=self.headers)
    if series_list is not None and len(series_list) > 0:
      return series_list
    else:
      return None

  def add_series(self, series_info, series_details):
      params = series_info
      params['languageProfileId'] = self.languageProfileId
      params['qualityProfileId'] = self.qualityProfileId
      params['addOptions'] = self.addOptions
      params['rootFolderPath'] = self.rootFolderPath
      params['seriesType'] = self.seriesType
      params['seasonFolder'] = self.seasonFolder
      params['monitored'] = self.monitored
      genres = series_details['genres']
      if genres is not None and len(genres) > 0:
        for genre in genres:
          for t in self.genreMappingPath:
            if genre in t['genre']:
              params['rootFolderPath'] = t['rootFolderPath']
              params['seriesType'] = t['seriesType']
      api = '/api/v3/series'
      r = self.req.post_and_return_content(self.server + api, params=json.dumps(params), headers=self.headers)
      r = json.loads(r)
      if 'errorMessage' in r:
        logger.error('Failed to add: {}', r['errorMessage'])
      elif 'title' in r:
        logger.info('Added: {}', r['title'])
        
  def search_series(self, search_key):
    api = '/api/v3/series/lookup'
    r = self.req.get_and_return_content(self.server + api, params={'term' :search_key }, headers=self.headers)
    if r is not None:
      return json.loads(r)
    else:
      return None

  def search_series_and_add(self, series_details, formatted_titles, original_title):
    original_title = series_details['original_title']
    imdb_id = series_details['imdb_id'].strip()
    found = False
    for idx, formatted_title in enumerate(formatted_titles):
      if found: 
        return
      found_series = self.search_series(format_series_title(formatted_title))
      if (found_series is not None) and (len(found_series) > 0):
        for series in  found_series:
          if ('imdbId' in series and series['imdbId'] == imdb_id) or ('cleanTitle' in series and series_title_match(series['cleanTitle'], original_title)):
            self.add_series(series, series_details)
            found = True
            break
      else:
        logger.info('Can\'t find the series with title {}', formatted_title)
      if (idx >= len(formatted_titles) ):
        logger.error('Failed to add：{}. There\'s no series matching the provided titles', series_details['title'])

  def does_series_exist(self, imdbId, original_titles):
    added_series = self.get_added_series()
    if added_series is not None:
      added_series = json.loads(added_series)
      for series in added_series:
        if ('imdbId' in series and series['imdbId'] == imdbId) or ('cleanTitle' in series and series_title_match(series['cleanTitle'], original_titles) or ('title' in series and series['title'] in original_titles) ) :
         return True
    return False