import sys
import os
import logging

logger = logging.getLogger(__name__)

from .http import HttpHandle
from .file import FileHandle

all_handles = {
  FileHandle.scheme: FileHandle,
  HttpHandle.scheme: HttpHandle,
}

__all__ = ["FileHandle", "HttpHandle", "all_handles"]
