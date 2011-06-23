import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
from ..utils import TarFile

from zope.interface import implements

class UpdateCommand:
  implements(ICommand)

  command = "update"

  usage = "update <stage> <version>"
  short = "Download and archive all the specified <stage>+<version>"
  docs  = """"""

  def setenv(self, env):
    self.env = env

  def validate(self, args):
    if len(args) != 2:
      raise RuntimeError, "Number of arguments must be exactly 2"
    if not self.env.contains(args[0]):
      raise RuntimeError, "Environment does not contain stage: " + args[0]
    return args

  def execute(self, stage, version):
    deploy = self.env.deploys.get(stage, None)

    if not deploy:
      logger.error("No such stage: " + stage)
      return False

    for module in deploy.modules:
      name = "{}-{}".format(module.name, version)

      path = self.env.archive.module_path(module, stage, version)

      if self.env.archive.contains(module, stage, version):
        print name, "already exists at", path
        continue

      handles = module.gethandles(version)

      tar  = TarFile(path)

      print name, "new", path

      try:
        for h in handles:
          print name, "adding", h.url.geturl()
          tar.download(h)
        print name, "saving"
        tar.commit()
      except RuntimeError, e:
        print name, "download failed:", str(e)
      finally:
        print name, "closing"
        tar.close()

    return True
