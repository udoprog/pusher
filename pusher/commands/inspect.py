import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
from ..utils import TarFile

from zope.interface import implements

class InspectCommand:
  implements(ICommand)

  command = "inspect"

  usage = "inspect [command]"
  short = "Inspect information about the running environment"
  docs  = """"""

  def setenv(self, env):
    self.env = env

  def validate(self, args):
    return args

  def execute(self, *args):
    for c in self.env.config:
      print "{0:20} = {1}".format(c, self.env.config.get(c))
