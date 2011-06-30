import sys
import os
import logging

logger = logging.getLogger(__name__)

class CompBase(object):
  "Group name, looked after in the root of the dictionary"
  __group__ = "base"

  "Required type keys"
  __keys__ = {}

  "Required configuration keys"
  __config_keys__ = {}

  def __init__(self, config):
    self.config = config

  def __getattr__(self, k):
    try:
      return self.__dict__[k]
    except KeyError:
      return self.config.get(k)

  def close(self):
    """
    Implement closing procedures for this resource.
    """
    pass
