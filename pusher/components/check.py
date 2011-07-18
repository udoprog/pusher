import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import CompBase

class Check(CompBase):
  __group__ = "checks"
  __keys__ = {
    "command": basestring
  }

  def __str__(self):
    return "{{{0}}} ({1})".format(self.command, self.name)
