import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
from .base import handle_stages
from ..utils import TarFile

from zope.interface import implements

class DeployCommand:
  implements(ICommand)

  command = "deploy"

  usage = "deploy <stage> <version>"
  short = "Deploy artifacts for <stage>+<version>"
  docs  = """See the pusher.yaml configuration for details."""

  def setenv(self, env):
    self.env = env

  def validate(self, args):
    if len(args) < 1:
      raise RuntimeError, "Number of arguments must be greater than zero"

    args = map(lambda a: tuple(a.split(":", 1)), args)
    return handle_stages(self.env, args)

  def execute(self, *stages):
    all_ok = True

    for (stage, version) in stages:
      deploy = self.env.deploys.get(stage)

      all_ok = True

      for server in deploy.servers:
        for module in deploy.modules:
          try:
            module.check(server)
          except Exception, e:
            print "Bad server {0}: {1}".format(server, str(e))
            all_ok = False

      for module in deploy.modules:
        if not self.env.archive.contains(module, stage, version):
          print "Not in archive (run update)", self.env.archive.module_path(module, stage, version)
          all_ok = False

    if not all_ok:
      return False

    for (stage, version) in stages:
      deploy = self.env.deploys.get(stage)

      for server in deploy.servers:
        for module in deploy.modules:
          server_root = server.config.get("server_root")

          source = self.env.archive.open(module, stage, version)

          if module.deploy_exists(server, source, deploy.name, version):
            print "Module {0} (version {1}-{2}) already exists at {3}".format(module.name, version, deploy.name, server)
            continue

          print "Deploying module {0} (version {1}-{2}) to {3} at {4}".format(module.name, version, deploy.name, server, server_root)

          try:
            module.deploy(server, source, deploy.name, version)
          finally:
            source.close()

    return True
