import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
from ..utils import TarFile

from zope.interface import implements

class HelpCommand:
  implements(ICommand)

  command = "help"

  usage = "help <command>"
  short = "Print docs for <command>"
  docs  = """"""

  def setenv(self, env):
    self.env = env

  def validate(self, args):
    if len(args) != 1:
      raise RuntimeError, "Number of arguments must be exactly 1"
    return args

  def execute(self, command):
    command = self.env.get_command(command)

    if not command:
      print >> sys.stderr, "No such command:", command
      return False

    print >> sys.stdout, "Usage:", command.usage
    print >> sys.stdout, "Short:", command.short
    print >> sys.stdout, command.docs
    return True
