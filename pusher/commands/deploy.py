import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
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

    all_ok = True

    for server in deploy.servers:
      for module in deploy.modules:
        try:
          module.check(server)
        except Exception, e:
          print "Bad server {}: {}".format(server, str(e))
          all_ok = False

    for module in deploy.modules:
      if not self.env.archive.contains(module, stage, version):
        print "Not in archive (run update)", self.env.archive.module_path(module, stage, version)
        all_ok = False

    if not all_ok:
      return False

    for server in deploy.servers:
      for module in deploy.modules:
        source = self.env.archive.open(module, stage, version)
        print "Deploying {} (version {}) to {}".format(deploy.name, version, server)

        try:
          module.deploy(server, source, deploy.name, version)
        finally:
          source.close()

    return True
