from .handles.base import IHandle
from zope.interface import implements

import logging

logger = logging.getLogger(__name__)

class ExtHandle:
  implements(IHandle)

  def __init__(self, name, size, mtime, mimetype, fileobj):
    self.name = name
    self.size = size
    self.mtime = mtime
    self.mimetype = mimetype
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
  import mimetypes

  mimetypes.init()

  if not config.get("zip_unpack", False):
    yield handle
    return

  logger.info("Extracting since zip_unpack = true");

  z = zipfile.ZipFile(handle.fileobj)

  def convert(dt):
    """
    Convert a ZipInfo date_time into a unix timestamp (compatible with tar).
    """
    return calendar.timegm(dt)

  for i in z.infolist():
    mime = mimetypes.guess_type(i.filename)[0]
    yield ExtHandle(i.filename, i.file_size, convert(i.date_time), mime, z.open(i))

  return

extlibs = {
  'application/zip': ziplib
}

__all__ = ["extlibs"]
