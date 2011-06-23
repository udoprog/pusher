import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
from ..utils import TarFile

from zope.interface import implements

class CheckCommand:
  implements(ICommand)

  command = "check"

  usage = "check <stage>"
  short = "Execute all configured checks for a specific <stage>."
  docs  = """See the pusher.yaml configuration for details."""

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

    i = 0

    ok = True

    for server in deploy.servers:
      for check in deploy.checks:
        line = "Check #{:03} {}:".format(i, check.name)
        if server.pretty_run(check.command, line=line) != 0:
          ok = False
        i += 1

    return ok
