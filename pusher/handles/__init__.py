import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import IHandle
from .http import HttpHandle
from .http import HttpsHandle
from .file import FileHandle
from .sftp import SftpHandle

all_handles = [
  FileHandle,
  HttpHandle,
  HttpsHandle,
  SftpHandle,
]

def import_name(full):
  module, name = full.split("#", 1)
  mm = module.split(".")[1:]

  try:
    m = __import__(module)
    for mi in mm:
      m = getattr(m, mi)
    klass = getattr(m, name)
  except:
    raise RuntimeError, "{}: no such module found".format(full)

  if not IHandle.implementedBy(klass):
    raise RuntimeError, "{}: does not implement IHandle".format(klass)

  all_handles.append(klass)

handle_cache = dict()
handle_size = 0

def find_handle(scheme):
  if handle_size != len(all_handles):
    for h in all_handles:
      handle_cache[h.scheme] = h
  return handle_cache.get(scheme, None)

__all__ = ["find_handle", "import_name"]
