import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
from .base import check_stage
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
    check_stage(self.env, args[0])
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
        line = "Check #{0:03} {1}:".format(i, check.name)
        if server.pretty_run(check.command, line=line) != 0:
          ok = False
        i += 1

    return ok
