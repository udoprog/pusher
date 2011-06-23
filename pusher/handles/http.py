import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import BaseHandle

class HttpHandle(BaseHandle):
  scheme = "http"

  module_version_header = "X-Pusher-Version"

  def __init__(self, url, version, config):
    self.url = url
    self.actual_url = None
    self.version = version
    self.config = config

    self.user_agent = config.get("http_user_agent", "Pusher/2.0")
    self.use_cookies = config.get("http_use_cookies", True)
    self.send_version = config.get("http_send_version", True)
    self.default_name = config.get("http_default_name", "index")

    self.requested = False

    self.size = None
    self.fileobj = None
    self._temp_path = None
    self._content_type = None

  def _request(self):
    import httplib
    import urlparse
    import shutil
    import Cookie

    cookie = None

    redirects = list()

    url = self.url

    def copy_to_temp(response):
      import tempfile
      (fd, path) = tempfile.mkstemp()

      try:
        fp = os.fdopen(fd, "w")
        shutil.copyfileobj(response, fp)
        self.fd_path = path
      except:
        os.fdclose(fd)
        os.remove(path)
        raise
        
      return fp, path

    while True:
      conn = httplib.HTTPConnection(url.netloc)

      try:
        conn.putrequest("GET", url.path)
        conn.putheader("User-Agent", self.user_agent)

        if self.send_version:
          conn.putheader("X-Pusher-Version", self.version)

        if cookie and self.use_cookies:
          if url.netloc.endswith(cookie.domain):
            logger.debug("Sending cookie: {}".format(cookie.coded_value))
            conn.putheader("Cookie", cookie.coded_value)
        
        conn.endheaders()
        response = conn.getresponse()
      finally:
        conn.close()

      loc = response.getheader("location")

      set_cookie = response.getheader("set-cookie")

      if set_cookie and self.use_cookies:
        cookie = Cookie.SimpleCookie(set_cookie)
        logger.debug("Setting cookie: {}".format(set_cookie))

      if loc:
        # parse the redirect location and perform a new request
        if loc in redirects:
          raise RuntimeError, "circular redirects"
        logger.debug("Redirecting to {}".format(loc))
        url = urlparse.urlparse(loc)
        redirects.append(loc)
        continue

      if response.status != 200:
        raise RuntimeError, "status code is not 200"

      self.actual_url = url
      self._content_type = response.getheader("content-type")

      if self._content_type:
        self._content_type = self._content_type.split(";")[0]

      # download the entire file to a local temporary file
      self.fileobj, self._temp_path = copy_to_temp(response)
      self.size = self.fileobj.tell()
      self.fileobj.seek(0)
      break

    self.requested = True

  def getfileobj(self):
    """
    return a file object
    """

    if not self.requested:
      self._request()

    if self.fileobj is None:
      raise RuntimeError, "fileobj is not available"

    return self.fileobj

  def getsize(self):
    if not self.requested:
      self._request()

    if self.size is None:
      raise RuntimeError, "size is not available"

    return self.size

  def getname(self):
    import mimetypes
    mimetypes.init()

    if not self.requested:
      self._request()

    if self.actual_url is None:
      raise RuntimeError, "name is not available"

    name = self.actual_url.path.split("/")[-1]

    ext = mimetypes.guess_extension(self._content_type)

    if name == "":
      name = self.default_name

    if ext is None or name.endswith(ext):
      return name

    return name + ext

  def getmtime(self):
    import time
    return time.time()

  def close(self):
    if self.fileobj:
      self.fileobj.close()
      os.remove(self._temp_path)

    self.fileobj = None
    self._temp_path = None
    self.size = None

