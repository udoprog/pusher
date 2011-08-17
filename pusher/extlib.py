from .handles.base import IHandle
from zope.interface import implements

import logging

logger = logging.getLogger(__name__)

class ExtHandle:
  implements(IHandle)

  def __init__(self, name, size, mtime, fileobj):
    self.name = name
    self.size = size
    self.mtime = mtime
    self.fileobj = fileobj

  def request(self):
    pass

  def close(self):
    pass

def ziplib(config, handle):
  """
  Function to unpack a downloaded zip file by exploding it into multiple handles.
  zip_unpack: Unpack if true
  """
  import zipfile
  import calendar

  if not config.get("zip_unpack", False):
    yield handle
    return

  logger.info("Unpacking zip since zip_unpack = true")

  zipfile = zipfile.ZipFile(handle.fileobj)

  def convert_date_time(dt):
    """
    Convert a ZipInfo date_time into a unix timestamp (compatible with tar).
    """
    return calendar.timegm(dt)

  for info in zipfile.infolist():
    yield ExtHandle(info.filename, info.file_size, convert_date_time(info.date_time), zipfile.open(info))

  return

extlibs = {
  'zip': ziplib
}

__all__ = ["extlibs"]
