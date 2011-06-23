from cStringIO import StringIO

import logging
logger = logging.getLogger(__name__)

import paramiko

def _safe_warp(name, func, *args, **kw):
  try:
    func(*args, **kw)
  except Exception, e:
    logger.error("Failed to execute {}: {}".format(name, str(e)))

class SFTPClient:
  def __init__(self, sftp):
    self.sftp = sftp

  def chdir(self, path):
    self.sftp.chdir(path)

  def mkdir(self, path):
    logger.info("checking directory: {}".format(path))

    try:
      st = self.sftp.stat(path)
    except Exception, e:
      logger.info("creating directory: {}".format(path))
      try:
        self.sftp.mkdir(path)
      except Exception, e:
        raise RuntimeError, "Failed to create directory {}: {}".format(path, str(e))

  def upload(self, fp, path):
    import shutil
    target = self.sftp.open(path, "w")

    try:
      shutil.copyfileobj(fp, target)
    finally:
      target.close()

  def download(self, fp, path):
    import shutil
    target = self.sftp.open(path, "r")

    try:
      shutil.copyfileobj(target, fp)
    finally:
      target.close()

  def upload_string(self, s, path):
    from cStringIO import StringIO
    fp = StringIO(s)

    try:
      self.upload(fp, path)
    except:
      fp.close()
      raise

  def touch(self, path):
    self.upload_string("", path)

  def download_string(self, path):
    from cStringIO import StringIO
    fp = StringIO()

    try:
      self.download(fp, path)
      return fp.getvalue()
    except:
      fp.close()
      raise

  def open(self, path, mode="r"):
    return self.sftp.open(path, mode)

  def is_file(self, path):
    import stat

    try:
      st = self.sftp.stat(path)
    except:
      return False
    
    return stat.S_ISREG(st.st_mode)

  def is_dir(self, path):
    import stat

    try:
      st = self.sftp.stat(path)
    except:
      return False
    
    return stat.S_ISDIR(st.st_mode)

  def is_sym(self, path):
    import stat

    try:
      st = self.sftp.lstat(path)
    except:
      return False
    
    return stat.S_ISLNK(st.st_mode)
  
  def rename(self, path, to, safe=False):
    if safe:
      _safe_wrap("rename", self.sftp.rename, path, to)
      return
    self.sftp.rename(path, to)

  def remove(self, path):
    self.sftp.remove(path)

  def rmdir(self, path, safe=False):
    if safe:
      _safe_wrap("rmdir", self.sftp.rmdir, path)
      return

    self.sftp.rmdir(path)

  def symlink(self, source, dest):
    self.sftp.symlink(source, dest)

  def normalize(self, path):
    return self.sftp.normalize(path)

class SSHClient:
  def __init__(self, ssh_address, **config):
    self.ssh = None
    self.timeout         = config.get("ssh_timeout", 5)
    self.bufsize         = config.get("ssh_bufsize", 2 ** 20)
    self.io_sleep        = config.get("ssh_io_sleep", 0.1)
    self.io_sleep_limit  = int(self.timeout / self.io_sleep)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    kw = dict()

    if "ssh_private_key" in config:
      private_key = config.get("ssh_private_key")

      try:
        kw["pkey"] = paramiko.DSSKey.from_private_key_file(private_key)
      except Exception, e:
        logger.warning("Could not open private key: {}".format(private_key, str(e)))

    if "ssh_username" in config:
      kw["username"] = config.get("ssh_username")
    if "ssh_password" in config:
      kw["password"] = config.get("ssh_password")

    try:
      ssh.connect(ssh_address, **kw)
    except Exception, e:
      raise RuntimeError, "connect to {} failed: {}".format(ssh_address, str(e))

    self.ssh = ssh
    self.transport = self.ssh.get_transport()

  def open_sftp(self):
    import paramiko
    sftp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())
    return SFTPClient(sftp)

  def connected(self):
    return self.ssh != None

  def close(self):
    self.transport.close()
    self.ssh.close()

  def run(self, command):
    import time

    if not self.connected():
      raise RuntimeError, "not connected"

    logger.debug("getting transport")
    chan = self.transport.open_session()

    stdout = StringIO()
    stderr = StringIO()
    
    try:
      chan.settimeout(float(self.timeout))
      chan.exec_command(command + "\n")

      i = 0

      # flush both stdout, stderr and wait for exitcode
      while not chan.exit_status_ready() or (chan.recv_ready() or chan.recv_stderr_ready()):
        if chan.recv_ready():
          stdout.write(chan.recv(self.bufsize))
          continue

        if chan.recv_stderr_ready():
          stderr.write(chan.recv_stderr(self.bufsize))
          continue

        time.sleep(self.io_sleep)
        if i < self.io_sleep_limit:
          i += 1
        else:
          raise RuntimeError, "ssh_timeout reached"

      return chan.recv_exit_status(), stdout.getvalue(), stderr.getvalue()
    finally:
      chan.close()
      stdout.close()
      stderr.close()
