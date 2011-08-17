import sys
import os
import logging

logger = logging.getLogger(__name__)

from zope.interface import Interface, Attribute

class IHandle(Interface):
  scheme   = Attribute("The supported scheme for this handle")
  url      = Attribute("""The requested url""")
  version  = Attribute("""The requested version""")
  config   = Attribute("""The associated configuration""")

  fileobj  = Attribute("""File object""")
  size     = Attribute("""File size""")
  name     = Attribute("""File name""")
  mimetype = Attribute("""Mime type, might be None""")

  def request(self):
    """
    Populate the fileobj, size and name
    """

  def close(self):
    """
    Close all information available on handle.
    """
