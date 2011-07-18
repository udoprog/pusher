import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import CompBase
from ..ssh import SSHClient

class Server(CompBase):
  __group__ = "servers"
  __keys__ = {  }
  __config_keys__ = {
    "address": basestring,
    "server_root": basestring,
  }

  server_check_file_default = ".pusher"

  def __init__(self, config):
    self._ssh_connection = None
    CompBase.__init__(self, config)

  def pretty_run(self, command, line="#: ", stream=sys.stdout, client=None):
    if client is None:
      client = self.connect()

    print >> stream, line, "Running", command, "on", self
    exitcode, stdout, stderr = client.run(command)

    def print_out(name, s):
      for l in s.split("\n"):
        if l.strip() == "": l = "(empty)"
        print >> stream, line, name, l

    if stdout: print_out("stdout:", stdout)
    if stderr: print_out("stderr:", stderr)

    print >> stream, line, "Exited with", exitcode
    
    if exitcode != 0:
      logger.info("Returned non-zero exit status")

    return exitcode

  def connect(self):
    """
    If a connection to the server is active, re-use it.
    Otherwise open and cache a new one.
    """
    if self._ssh_connection:
      logger.debug("Reusing cached connection")
      return self._ssh_connection

    logger.debug("Initializing new connection to {0}".format(self))
    self._ssh_connection = SSHClient(self.address, self.config)
    return self._ssh_connection

  def close(self):
    """
    If a connection to the server is active, close it.
    """
    if self._ssh_connection:
      self._ssh_connection.close()
      self._ssh_connection = None

  def __str__(self):
    return "{0} ({1})".format(self.address, self.name)

