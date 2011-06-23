import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import CompBase, config_format

class Check(CompBase):
  __group__ = "checks"
  __keys__ = {
    "command": basestring
  }

  def run(self, env, server):
    import time

    logger.info("Check {} on {}".format(self, server))

    client = server.connect()

    return client.run(self.command)

  def __str__(self):
    return "{{{}}} ({})".format(self.command, self.name)
