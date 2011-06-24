import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import IHandle

from zope.interface import implements

def create_http_connection(url):
  import httplib
  return httplib.HTTPConnection(url.netloc)

def create_https_connection(url):
  import httplib
  return httplib.HTTPSConnection(url.netloc)

def http_request(create_connection):
  def req(handle):
    import time

    if handle.requested:
      raise RuntimeError, "already requested url"

    handle.requested = True

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
        name = handle.default_name

      if ext is None or name.endswith(ext):
        return name

      return name + ext

    def request_redirects(url):
      import Cookie
      import urlparse

      redirects = list()
      cookie    = None

      while True:
        conn = create_connection(url)

        try:
          conn.putrequest("GET", url.path)
          conn.putheader("User-Agent", handle.user_agent)

          if handle.send_version:
            conn.putheader("X-Pusher-Version", handle.version)

          if cookie and handle.use_cookies:
            for key, item in cookie.items():
              if "domain" in item and not url.netloc.endswith(item["domain"]):
                continue
              
              if "path" in item and not url.path.startswith(item["path"]):
                continue

              logger.debug("Sending cookie: {}".format(item.coded_value))
              conn.putheader("Cookie", item.coded_value)
          
          conn.endheaders()
          response   = conn.getresponse()

          location   = response.getheader("location")
          set_cookie = response.getheader("set-cookie")

          if set_cookie and handle.use_cookies:
            logger.debug("Setting cookie: {}".format(set_cookie))
            cookie = Cookie.SimpleCookie()
            cookie.load(set_cookie)

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

    url, conn, response = request_redirects(handle.url)

    try:
      if response.status != 200:
        raise RuntimeError, "status code is not 200"

      content_type = response.getheader("content-type")

      if content_type:
        content_type = content_type.split(";", 1)[0]

      # download the entire file to a local temporary file
      handle.fileobj, handle.temp = copy_to_temp(response)
      handle.size               = handle.fileobj.tell()
      handle.name               = get_name(url, content_type)
      handle.mtime              = time.time()

      handle.fileobj.seek(0)
    finally:
      conn.close()

  return req

def http_close():
  def close(self):
    if self.fileobj:
      self.fileobj.close()
      os.remove(self.temp)

    self.fileobj = None
    self.temp    = None
    self.size    = None
  return close

class HttpHandle:
  implements(IHandle)

  scheme = "http"

  module_version_header = "X-Pusher-Version"

  request = http_request(create_http_connection)
  close   = http_close()

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

class HttpsHandle(HttpHandle):
  implements(IHandle)

  scheme = "https"

  module_version_header = "X-Pusher-Version"

  request = http_request(create_https_connection)
  close   = http_close()

  def __init__(self, url, version, config):
    self.url          = url
    self.version      = version
    self.config       = config

    self.user_agent   = config.get("https_user_agent", "Pusher/2.0")
    self.use_cookies  = config.get("https_use_cookies", True)
    self.send_version = config.get("https_send_version", True)
    self.default_name = config.get("https_default_name", "index")

    self.size         = None
    self.fileobj      = None
    self.name         = None
    self.mtime        = None

    self.requested    = False
    self.temp         = None
