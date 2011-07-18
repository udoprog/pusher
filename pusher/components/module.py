import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import CompBase
from ..handles import find_handle
from StringIO import StringIO

class Module(CompBase):
  __group__ = "modules"
  __keys__ = {
    "urls": list,
  }

  releases_path = "releases"
  revision_path = "revision"
  current_path  = "current"

  def gethandles(self, version):
    import urlparse

    config = self.config.sub(version=version)

    def urls():
      for url in config.get("urls"):
        yield urlparse.urlparse(url)

    def handles():
      # initialize all urls
      for url in list(urls()):
        handle = find_handle(url.scheme)

        if handle is None:
          raise RuntimeError, "No handle available for scheme: " + url.scheme

        yield handle(url, version, self.config)

    # initialize all handles
    for h in list(handles()):
      yield h

  def _setup_root(self, server, sftp):
    import yaml

    deploy_root = os.path.join(server.server_root, self.name)
    sftp.mkdir(deploy_root)
    sftp.chdir(deploy_root)
    sftp.mkdir(self.releases_path)

    return deploy_root

  def _setup_paths(self, version, deploy_name):
    rr = (self.releases_path, version, deploy_name)
    release_path = "{0}/{1}-{2}".format(*rr)
    release_tmp  = "{0}/.{1}-{2}.tmp".format(*rr)
    release_tar  = "{0}/{1}-{2}.tar".format(*rr)
    return release_path, release_tmp, release_tar

  def check(self, server):
    client = server.connect()
    sftp = client.open_sftp()

    if not sftp.is_dir(server.server_root):
      raise RuntimeError, "Server root does not exist (run setup): " + server.server_root

    server_check_file = server.config.get("server_check_file", server.server_check_file_default)
    server_check = "{0}/{1}".format(server.server_root, server_check_file)

    if not sftp.is_file(server_check):
      raise RuntimeError, "Server check does not exist (run setup): " + server_check

  def setup(self, server):
    client = server.connect()
    sftp = client.open_sftp()

    if not sftp.is_dir(server.server_root):
      sftp.mkdir(server.server_root)

    server_check = "{0}/{1}".format(server.server_root, server.server_check)

    if not sftp.is_file(server_check):
      sftp.touch(server_check)

    deploy_root = self._setup_root(server, sftp)

  def exists(self, server):
    client = server.connect()
    sftp = client.open_sftp()

    if not sftp.is_dir(server.server_root):
      logger.debug("Missing: {0}".format(server.server_root))
      return False

    server_check = "{0}/{1}".format(server.server_root, server.server_check)

    if not sftp.is_file(server_check):
      logger.debug("Missing: {0}".format(server_check))
      return False

    deploy_root = os.path.join(server.server_root, self.name)

    if not sftp.is_dir(deploy_root):
      logger.debug("Missing: {0}".format(deploy_root))
      return False

    sftp.chdir(deploy_root)

    if not sftp.is_dir(self.releases_path):
      logger.debug("Missing: {0}".format(self.releases_path))
      return False

    return True

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

    release_full = "{0}/{1}".format(root, release_path)

    if not sftp.is_dir(release_path):
      raise RuntimeError, "release not available - missing deploy?"

    if sftp.is_sym(self.current_path):
      if sftp.normalize(self.current_path) == release_full:
        logger.info("Release already checked out")
      else:
        sftp.remove(self.current_path)
        sftp.symlink(release_path, self.current_path)

    logger.info("Uploading revision string")
    revision_str = "{0}:{1}".format(deploy_name, version)
    sftp.upload_string(revision_str, self.revision_path)
    sftp.symlink(release_path, self.current_path)

  def current(self, server):
    client = server.connect()
    sftp = client.open_sftp()
    root = self._setup_root(server, sftp)

    if not sftp.is_file(self.revision_path):
      return None, None

    revision_str = sftp.download_string(self.revision_path)
    if not ":" in revision_str:
      return None, None
    return revision_str.split(":", 1)

  def deploy_exists(self, server, source, deploy_name, version):
    client = server.connect()
    sftp = client.open_sftp()
    root = self._setup_root(server, sftp)

    release_path, release_tmp, release_tar = self._setup_paths(version, deploy_name)

    if not sftp.is_file(release_tar):
      return False

    if not sftp.is_dir(release_path):
      return False

    return True

  def deploy(self, server, source, deploy_name, version):
    client = server.connect()
    sftp = client.open_sftp()
    root = self._setup_root(server, sftp)

    release_path, release_tmp, release_tar = self._setup_paths(version, deploy_name)

    if sftp.is_file(release_tar) and sftp.is_dir(release_path):
      logger.info("Nothing to deploy, release path exists")
      return

    if sftp.is_dir(release_path):
      logger.debug("Removing stale release_path")
      remove_cmd = "cd {0} && rm -rf {1}".format(root, release_path)

      exitcode, stdout, stderr = client.run(remove_cmd)

      if exitcode != 0:
        raise RuntimeError, "Failed to remove release_path"

    sftp.mkdir(release_tmp)

    try:
      if not sftp.is_file(release_tar):
        logger.info("Uploading: {0}".format(release_tar))
        sftp.upload(source, release_tar)

      logger.info("Extracting archive")
      unpack_cmd = "cd {0} && tar -C \"{1}\" -xvf \"{2}\"".format(root, release_tmp, release_tar)
      exitcode, stdout, stderr = client.run(unpack_cmd)

      if exitcode != 0:
        raise RuntimeError, "Failed to extract archive"

      sftp.rename(release_tmp, release_path)
    except:
      sftp.rmdir(release_tmp, safe=True)
      raise

  def __str__(self):
    return "{0} ({1})".format(self.urls, self.name)

