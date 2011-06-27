import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
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
    if not self.env.contains(args[0]):
      raise RuntimeError, "Environment does not contain stage: " + args[0]
    return args

  def execute(self, stage):
    deploy = self.env.deploys.get(stage, None)

    if not deploy:
      logger.error("No such stage: " + stage)
      return False

    for server in deploy.servers:
      for module in deploy.modules:
        print "Setting up module", module.name, "at", server
        module.setup(server)

    return True
