import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import IHandle
from ..ssh import SSHClient

from zope.interface import implements

class SftpHandle:
  implements(IHandle)

  scheme = "sftp"

  def __init__(self, url, version, config):
    self.url       = url
    self.version   = version
    self.config    = config

    self.size      = None
    self.fileobj   = None
    self.name      = None
    self.mtime     = None
    self.mimetype  = None

    self.requested = False
    self.temp      = None
  
  def request(self):
    import tempfile
    import mimetypes

    mimetypes.init()

    if self.requested:
      raise RuntimeError, "handle already requested"
    self.requested = True

    ssh = SSHClient(self.url.netloc, self.config)
    sftp = ssh.open_sftp()

    if not sftp.is_file(self.url.path):
      raise RuntimeError, "not a file"

    (fd, self.temp) = tempfile.mkstemp()

    self.fileobj = os.fdopen(fd, "w")
    self.size    = self.fileobj.tell()
    self.mtime   = sftp.mtime(self.url.path)
    self.name    = self.url.path.split("/")[-1]
    self.mimetype = mimetypes.guess_type(self.name)[0]

    sftp.download(self.fileobj, self.url.path)

    self.fileobj.seek(0)

  def close(self):
    if self.fileobj:
      self.fileobj.close()
      os.remove(self.temp)

    self.fileobj = None
    self.temp = None
    self.size = None
    self.mtime = None
