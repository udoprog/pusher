import os
import sys
import logging

logger = logging.getLogger(__name__)

from .ssh import SSHClient

class TarFile:
  def __init__(self, archive, module, stage, version):
    import tarfile
    import tempfile

    self.archive = archive
    self.module = module
    self.stage = stage
    self.version = version

    self.not_finished = False

    (fd, self.path) = tempfile.mkstemp(".tar")
    self.fp = os.fdopen(fd, "w")
    self.tarfile = tarfile.open(mode="w", fileobj=self.fp)

  def unfinished(self):
    self.not_finished = True
  
  def download(self, url):
    from cStringIO import StringIO
    import tarfile
    import shutil
    import tempfile

    name = os.path.basename(url.path)

    sp = self.module.open(self.version, url)

    info = tarfile.TarInfo(sp.getname())
    info.mtime = sp.getmtime() 
    info.size = sp.getsize()

    logger.debug("Adding to tar: {}".format(info.name))

    try:
      self.tarfile.addfile(info, sp.getfileobj())
    finally:
      sp.close()

  def close(self):
    if self.not_finished:
      os.remove(self.path)
      return

    try:
      p = self.archive.module_path(self.module, self.stage, self.version)
      os.rename(self.path, p)
    finally:
      self.fp.close()

class Archive:
  def __init__(self, env, path):
    self.env = env
    self.path = path

  def create(self):
    path = os.path.join(self.env.root, self.path)
    if not os.path.isdir(path):
      os.mkdir(path)

  def new_tar(self, module, stage, version):
    return TarFile(self, module, stage, version)

  def module_path(self, m, s, v):
    return os.path.join(self.env.root, self.path, "{}-{}-{}".format(v, s, m.name))

  def open(self, m, s, v):
    return open(self.module_path(m, s, v), "r")

  def contains(self, module, stage, version):
    return os.path.isfile(self.module_path(module, stage, version))

__all__ = ["Archive"]
