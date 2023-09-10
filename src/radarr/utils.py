import json

from loguru import logger

from src.utils.http_utils import RequestUtils

class Radarr:
  def __init__(self, host=None, port=None, url_base=None, api_key=None, is_https=False, rootFolderPath="/media/电影",qualityProfileId=1, addOptions ={},minimumAvailability= '', monitored= ''  ):
      self.req = RequestUtils(request_interval_mode=True, max_attempt=6, min_request_interval_in_ms=200, max_request_interval_in_ms=500, min_sleep_secs=0.1, max_sleep_secs=0.2)
      self.host = host
      self.port = port
      self.url_base = url_base
      self.rootFolderPath = rootFolderPath
      self.qualityProfileId = qualityProfileId
      self.addOptions = addOptions
      self.minimumAvailability = minimumAvailability
      self.monitored = monitored
      self.headers={
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
      }
      self.server = '%s://%s%s%s' % ("https" if is_https else "http", host, ":" if url_base == "" else "", port if url_base == "" else url_base)
      self.added_movies = self.get_added_movies()

  def get_added_movies(self):
    api = '/api/v3/movie'
    r = self.req.get_and_return_content(self.server + api, headers=self.headers)
    if r is not None:
      return json.loads(r)
    else:
      logger.warning("Trying to get the added movies but the result is none")
      return None

  def does_movie_exist(self, imdb_id):
    if self.added_movies is not None:
      for movie in self.added_movies:
        if ('imdbId' in movie and movie['imdbId'] == imdb_id):
          return True
    return False

  def search_movie(self, title):
    api = '/api/v3/movie/lookup'
    r = self.req.get_and_return_content(self.server + api, params={'term':title}, headers=self.headers)
    if r is not None:
      return json.loads(r)
    else:
      return None

  def add_movie(self, movie_info):
    api = '/api/v3/movie'
    params = movie_info
    params['qualityProfileId'] = self.qualityProfileId
    params['rootFolderPath'] = self.rootFolderPath
    params['monitored'] = self.monitored
    params['addOptions'] = self.addOptions
    params['minimumAvailability'] = self.minimumAvailability
    r = self.req.post_and_return_content(self.server + api, params=json.dumps(params), headers=self.headers)
    r = json.loads(r)
    if 'title' in r and r['title'] == movie_info['title'] or r['originalTitle'] == movie_info['originalTitle']:
      logger.info('Successfully added: {}', (movie_info['title']))
    else:
      logger.error('Failed to add: {}', (movie_info['title']))

  def search_movie_and_add(self, title, imdb_id):
    found_movies = []
    try:
      found_movies = self.search_movie('imdb:' + imdb_id)
      if not isinstance(found_movies, list): 
        raise Exception('Exceptions in requests')
    except Exception as e:    
      found_movies = self.search_movie(title)
    if found_movies is not None and len(found_movies) > 0:
      for idx,result in enumerate(found_movies):
        if 'imdbId' in result and result['imdbId'] == imdb_id:
          self.add_movie(result)
          break
        if idx >= len(found_movies):
          logger.error('Failed to add {}', title)
    else:
      logger.warning('Can\'t find movie {}', title)