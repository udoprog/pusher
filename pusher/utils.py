import sys
import os
import logging

logger = logging.getLogger(__name__)

from .handles.base import IHandle
from .extlib import extlibs

class TarFile:
  default_dir_permissions  = "755"
  default_file_permissions = "644"

  def __init__(self, config, path):
    import tarfile
    import tempfile

    self.config  = config
    self.path    = path
    self.temp    = path + ".tmp"

    self.fp      = open(self.temp, "w")
    self.tar     = tarfile.open(mode="w", fileobj=self.fp)

    self.file_permissions = int(config.get("tar_file_permissions", self.default_file_permissions), 8)
    self.dir_permissions = int(config.get("tar_dir_permissions", self.default_dir_permissions), 8)
  
  def download(self, handle):
    from cStringIO import StringIO
    import shutil
    import tempfile

    if not IHandle.providedBy(handle):
      raise RuntimeError, "{0} does not provide IHandle".format(repr(handle))

    try:
      handle.request()
    except Exception, e:
      raise RuntimeError, "Failed to request handle: {0}".format(e)

    logger.info("Mime is '{0}'".format(handle.mimetype))

    if handle.mimetype in extlibs:
      logger.info("Using extlib for mime '{0}'".format(handle.mimetype))
      for h in extlibs[handle.mimetype](self.config, handle):
        self.add_handle(h)
    else:
      self.add_handle(handle)

  def add_handle(self, handle):
    import tarfile

    info       = tarfile.TarInfo(handle.name)

    # directories must have mode 775
    if info.name.endswith("/"):
      info.mode = self.dir_permissions
      info.type = tarfile.DIRTYPE
    else:
      info.mode = self.file_permissions
      info.type = tarfile.REGTYPE

    info.mtime = handle.mtime
    info.size  = handle.size

    logger.info("Adding to tar: {0} ({1} bytes)".format(info.name, info.size))

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

