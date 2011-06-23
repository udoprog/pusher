import sys
import os
import logging

logger = logging.getLogger(__name__)

def config_format(s, config, **kw):
  if len(kw) > 0:
    d = dict(config)
    d.update(kw)
  else:
    d = config

  try:
    return s.format(**d)
  except KeyError, e:
    raise RuntimeError, "format failed for key: " + str(e)

class CompBase(object):
  __group__ = "base"
  __keys__ = {}
  __noformat__ = set([])

  def __init__(self, config):
    self.name = config.get("name")
    self.config = config

  def set_attr(self, k, v):
    if isinstance(v, basestring) and k not in self.__noformat__:
      v = config_format(v, self.config)
    setattr(self, k, v)

  def close(self):
    """
    Implement closing procedures for this resource.
    """
    pass
