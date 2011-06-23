import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import IHandle

from zope.interface import implements

class HttpHandle:
  implements(IHandle)

  scheme = "http"

  module_version_header = "X-Pusher-Version"

  def __init__(self, url, version, config):
    self.url          = url
    self.version      = version
    self.config       = config

    self.user_agent   = config.get("http_user_agent", "Pusher/2.0")
    self.use_cookies  = config.get("http_use_cookies", True)
    self.send_version = config.get("http_send_version", True)
    self.default_name = config.get("http_default_name", "index")

    self.size         = None
    self.fileobj      = None
    self.name         = None
    self.mtime        = None

    self.requested    = False
    self.temp         = None

  def request(self):
    import time
    import urlparse

    if self.requested:
      raise RuntimeError, "already requested url"

    self.requested = True

    def copy_to_temp(response):
      import tempfile
      import shutil

      (td, path) = tempfile.mkstemp()

      tempfile = os.fdopen(td, "w+")

      logger.debug("downloading to temporary file {}".format(path))

      try:
        shutil.copyfileobj(response, tempfile)
      except:
        logger.debug("removing temporary file {}".format(path))
        tempfile.close()
        os.remove(path)
        raise

      return tempfile, path

    def get_name(url, content_type):
      import mimetypes
      mimetypes.init()

      name = url.path.split("/")[-1]

      ext = mimetypes.guess_extension(content_type)

      if name == "":
        name = self.default_name

      if ext is None or name.endswith(ext):
        return name

      return name + ext

    def request_redirects(url):
      import Cookie
      import httplib

      redirects = list()
      cookie    = None

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
          response   = conn.getresponse()

          location   = response.getheader("location")
          set_cookie = response.getheader("set-cookie")

          if set_cookie and self.use_cookies:
            cookie = Cookie.SimpleCookie(set_cookie)
            logger.debug("Setting cookie: {}".format(set_cookie))

          if not location:
            return url, conn, response

          conn.close()

          # parse the redirect location and perform a new request
          if location in redirects:
            raise RuntimeError, "circular redirects"

          logger.debug("Redirecting to {}".format(location))
          url = urlparse.urlparse(location)
          redirects.append(location)
        except:
          conn.close()
          raise

    url, conn, response = request_redirects(self.url)

    try:
      if response.status != 200:
        raise RuntimeError, "status code is not 200"

      content_type = response.getheader("content-type")

      if content_type:
        content_type = content_type.split(";", 1)[0]

      # download the entire file to a local temporary file
      self.fileobj, self.temp = copy_to_temp(response)
      self.size               = self.fileobj.tell()
      self.name               = get_name(url, content_type)
      self.mtime              = time.time()

      self.fileobj.seek(0)
    finally:
      conn.close()

  def close(self):
    if self.fileobj:
      self.fileobj.close()
      os.remove(self.temp)

    self.fileobj = None
    self.temp    = None
    self.size    = None
