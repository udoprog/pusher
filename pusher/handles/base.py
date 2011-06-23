import sys
import os
import logging

logger = logging.getLogger(__name__)

class BaseHandle:
  def getfileobj(self):
    raise RuntimeError, "not implemented"
  def getsize(self):
    raise RuntimeError, "not implemented"
  def getname(self):
    raise RuntimeError, "not implemented"
  def getmtime(self):
    raise RuntimeError, "not implemented"
  def close(self):
    pass
