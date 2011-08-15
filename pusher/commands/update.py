import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
from .base import handle_stages
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
    if len(args) < 1:
      raise RuntimeError, "Number of arguments must be greater than 1"

    args = map(lambda a: tuple(a.split(":", 1)), args)
    return handle_stages(self.env, args)

  def execute(self, *stages):
    for (stage, version) in stages:
      deploy = self.env.deploys.get(stage, None)

      for module in deploy.modules:
        name = "{0}-{1}".format(module.name, version)

        path = self.env.archive.module_path(module, stage, version)

        if self.env.archive.contains(module, stage, version):
          print name, "already exists at", path
          continue

        handles = list(module.gethandles(version))

        if "before_update" in module.config:
          for h in handles:
            config = module.config.sub(url=h.url.geturl())
            self.env.run(config.get("before_update"))

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
