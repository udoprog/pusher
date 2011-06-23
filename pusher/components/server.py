import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import CompBase, config_format
from ..ssh import SSHClient

class Server(CompBase):
  __group__ = "servers"
  __keys__ = {
    "address": basestring,
    "server_root": basestring,
  }

  def __init__(self, config):
    self._ssh_connection = None
    CompBase.__init__(self, config)

  def connect(self):
    """
    If a connection to the server is active, re-use it.
    Otherwise open and cache a new one.
    """
    if self._ssh_connection:
      logger.debug("Reusing cached connection")
      return self._ssh_connection

    logger.debug("Initializing new connection to {}".format(self))
    self._ssh_connection = SSHClient(self.address, **self.config)
    return self._ssh_connection

  def close(self):
    """
    If a connection to the server is active, close it.
    """
    if self._ssh_connection:
      self._ssh_connection.close()
      self._ssh_connection = None

  def __str__(self):
    return "{} ({})".format(self.address, self.name)

