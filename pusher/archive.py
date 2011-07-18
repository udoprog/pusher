import os
import sys
import logging

logger = logging.getLogger(__name__)

from .handles.base import IHandle

class Archive:
  def __init__(self, env, path):
    self.env = env
    self.path = path

  def create(self):
    path = os.path.join(self.env.root, self.path)
    if not os.path.isdir(path):
      os.mkdir(path)

  def module_path(self, m, s, v):
    return os.path.join(self.env.root, self.path, "{0}-{1}-{2}".format(v, s, m.name))

  def open(self, m, s, v):
    return open(self.module_path(m, s, v), "r")

  def contains(self, module, stage, version):
    return os.path.isfile(self.module_path(module, stage, version))

__all__ = ["Archive"]
