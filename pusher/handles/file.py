import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import BaseHandle

class FileHandle(BaseHandle):
  scheme = "file"

  def __init__(self, url, version, config):
    self.url = url
    self.version = version
    self.config = config

  def getfileobj(self):
    return file(self.url.path, "r")

  def getsize(self):
    return os.path.getsize(self.url.path)

  def getname(self):
    return os.path.basename(self.url.path)

  def getmtime(self):
    return os.stat(self.url.path).st_mtime

