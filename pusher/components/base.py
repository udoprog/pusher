import sys
import os
import logging

logger = logging.getLogger(__name__)

class CompBase(object):
  __group__ = "base"
  __keys__ = {}
  __noformat__ = set([])

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
