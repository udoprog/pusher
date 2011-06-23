import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import CompBase, config_format
from ..handles import all_handles
from StringIO import StringIO

class Module(CompBase):
  __group__ = "modules"
  __keys__ = {
    "urls": list,
  }
  __noformat__ = set(["url"])

  releases_path = "releases"
  revision_path = "revision"
  current_path  = "current"

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

  def _setup_root(self, server, sftp):
    import yaml

    deploy_root = os.path.join(server.server_root, self.name)
    sftp.mkdir(deploy_root)
    sftp.chdir(deploy_root)
    sftp.mkdir(self.releases_path)

    return deploy_root

  def _setup_paths(self, version, deploy_name):
    rr = (self.releases_path, version, deploy_name)
    release_path = "{}/{}-{}".format(*rr)
    release_tmp  = "{}/.{}-{}.tmp".format(*rr)
    release_tar  = "{}/{}-{}.tar".format(*rr)
    return release_path, release_tmp, release_tar

  def checkout(self, server, deploy_name, version):
    client = server.connect()
    sftp = client.open_sftp()
    root = self._setup_root(server, sftp)

    if deploy_name is None or version is None:
      if sftp.is_sym(self.current_path):
        sftp.remove(self.current_path)
      if sftp.is_file(self.revision_path):
        sftp.remove(self.revision_path)
      return

    release_path, release_tmp, release_tar = self._setup_paths(version, deploy_name)

    release_full = "{}/{}".format(root, release_path)

    if not sftp.is_dir(release_path):
      raise RuntimeError, "release not available - missing deploy?"

    if sftp.is_sym(self.current_path):
      if sftp.normalize(self.current_path) == release_full:
        logger.info("Release already checked out")
        return

      sftp.remove(self.current_path)

    sftp.symlink(release_path, self.current_path)
    revision_str = "{}:{}".format(deploy_name, version)
    sftp.upload_string(revision_str, self.revision_path)

  def current(self, server):
    client = server.connect()
    sftp = client.open_sftp()
    root = self._setup_root(server, sftp)

    if not sftp.is_file(self.revision_path):
      return None, None

    revision_str = sftp.download_string(self.revision_path)
    return revision_str.split(":", 1)

  def deploy(self, server, source, deploy_name, version):
    client = server.connect()
    sftp = client.open_sftp()
    root = self._setup_root(server, sftp)

    release_path, release_tmp, release_tar = self._setup_paths(version, deploy_name)

    if sftp.is_dir(release_path):
      logger.info("Nothing to deploy, release path exists")
      return

    sftp.mkdir(release_tmp)

    try:
      if not sftp.is_file(release_tar):
        logger.info("Uploading: {}".format(release_tar))
        sftp.upload(source, release_tar)

      logger.info("Extracting archive")
      unpack_cmd = "cd {} && tar -C \"{}\" -xvf \"{}\"".format(root, release_tmp, release_tar)
      exitcode, stdout, stderr = client.run(unpack_cmd)

      if exitcode != 0:
        raise RuntimeError, "Failed to extract archive"

      sftp.rename(release_tmp, release_path)
    except:
      sftp.rmdir(release_tmp, safe=True)
      raise

  def __str__(self):
    return "{} ({})".format(self.urls, self.name)

