import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import CompBase, config_format
from ..handles import all_handles

class Module(CompBase):
  __group__ = "modules"
  __keys__ = {
    "urls": list,
  }
  __noformat__ = set(["url"])

  releases_path = "releases"
  revision_path = "revision"

  handles = all_handles

  def geturls(self, version):
    import urlparse
    l = list()

    cache = dict(self.config)
    cache["version"] = version

    for url in self.urls:
      l.append(urlparse.urlparse(config_format(url, cache)))

    return l

  def open(self, version, url):
    """
    Open the url and get a file-like object.
    """
    handle = self.handles.get(url.scheme, None)

    if handle is None:
      raise RuntimeError, "No handle available for scheme: " + url.scheme

    return handle(url, version, self.config)

  def _setup_root(self, server, sftp, deploy):
    import yaml

    def create_config():
      d = dict()
      d["releases"] = list()
      d["current"] = None
      return d

    deploy_root = os.path.join(server.server_root, self.name)
    sftp.mkdir(deploy_root)
    sftp.chdir(deploy_root)
    sftp.mkdir(self.releases_path)

    c = None

    try:
      fp = sftp.open(self.revision_path, "r")
      c = yaml.load(fp)
    except:
      c = create_config()
      sftp.upload_string(yaml.dump(c), self.revision_path)

    return c

  def _persist_root(self, sftp, revision):
    import yaml
    sftp.upload_string(yaml.dump(revision), self.revision_path)

  def deploy(self, server, source, deploy, version):
    client = server.connect()
    sftp = client.open_sftp()

    revision = self._setup_root(server, sftp, deploy)

    release_path = os.path.join(self.releases_path, "{}-{}.tar".format(version, deploy.name))

    rel = (release_path, deploy.name, version)

    if not sftp.is_file(release_path):
      sftp.upload(source, release_path)

    if rel not in revision["releases"]:
      revision["releases"].append(rel)
      self._persist_root(sftp, revision)

  def __str__(self):
    return "{} ({})".format(self.urls, self.name)

