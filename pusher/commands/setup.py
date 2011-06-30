import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
from .base import check_stage
from ..utils import TarFile

from zope.interface import implements

class SetupCommand:
  implements(ICommand)

  command = "setup"

  usage = "setup <stage>"
  short = "Setup all servers specified in <stage>"
  docs  = """"""

  def setenv(self, env):
    self.env = env

  def validate(self, args):
    if len(args) != 1:
      raise RuntimeError, "Number of arguments must be exactly 1"
    check_stage(self.env, args[0])
    return args

  def execute(self, stage):
    deploy = self.env.deploys.get(stage, None)

    if not deploy:
      logger.error("No such stage: " + stage)
      return False

    for server in deploy.servers:
      server_root = server.config.get("server_root")

      for module in deploy.modules:
        if module.exists(server):
          print "Module", module.name, "already exists at", server, "in", server_root
          continue

        print "Setting up module", module.name, "at", server, "in", server_root
        module.setup(server)

    return True
