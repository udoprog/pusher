import sys
import os
import logging

logger = logging.getLogger(__name__)

from .handles.base import IHandle

class TarFile:
  def __init__(self, path):
    import tarfile
    import tempfile

    self.path    = path
    self.temp    = path + ".tmp"

    self.fp      = open(self.temp, "w")
    self.tar     = tarfile.open(mode="w", fileobj=self.fp)
  
  def download(self, handle):
    from cStringIO import StringIO
    import tarfile
    import shutil
    import tempfile

    if not IHandle.providedBy(handle):
      raise RuntimeError, "{} does not provide IHandle".format(repr(handle))

    try:
      handle.request()
    except Exception, e:
      raise RuntimeError, "request failed: {}".format(str(e))

    info       = tarfile.TarInfo(handle.name)
    info.mtime = handle.mtime
    info.size  = handle.size

    logger.debug("Adding to tar: {}".format(info.name))

    try:
      self.tar.addfile(info, handle.fileobj)
    finally:
      handle.close()

  def close(self):
    self.tar.close()
    self.fp.close()

    if self.temp:
      os.remove(self.temp)
      self.temp = None

  def commit(self):
    os.rename(self.temp, self.path)
    self.temp = None

