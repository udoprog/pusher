import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
from .base import check_stage
from ..utils import TarFile

from zope.interface import implements

class CheckoutCommand:
  implements(ICommand)

  command = "checkout"

  usage = "checkout <stage> <version>"
  short = "Checkout artifacts for <stage>+<version>, symlinking to 'current'"
  docs  = """See the pusher.yaml configuration for details."""

  def setenv(self, env):
    self.env = env

  def validate(self, args):
    if len(args) != 2:
      raise RuntimeError, "Number of arguments must be exactly 2"
    check_stage(self.env, args[0])
    return args

  def execute(self, stage, version):
    deploy = self.env.deploys.get(stage, None)

    if not deploy:
      logger.error("No such stage: " + stage)
      return False

    all_ok = True
    for server in deploy.servers:
      for module in deploy.modules:
        try:
          module.check(server)
        except Exception, e:
          print "Bad server {}: {}".format(server, str(e))
          all_ok = False

    if not all_ok:
      return False

    previous = list()
    changed = list()

    print "Downloading rollback states"

    for server in deploy.servers:
      for module in deploy.modules:
        previous.append(((server, module), module.current(server)))
        changed.append(False)

    # run as little as possible with terminal errors
    for i, ((server, module), (current_name, current_version)) in enumerate(previous):
      if "before_checkout" in module.config:
        print "Triggering", module.name, "{before_checkout} on", server
        code = server.pretty_run(module.config.get("before_checkout"))
        if code != 0:
          print "before_checkout: non-zero exit status"
          return False

    for i, ((server, module), (current_name, current_version)) in enumerate(previous):
      name="{} (version {}-{}) on {}".format(module.name, deploy.name, version, server)

      if current_name == deploy.name and current_version == version:
        print("{}: {}".format(name, "Already checked out"))
        changed[i] = True
        continue

      print("{}: {}".format(name, "Checking out"))

      try:
        module.checkout(server, deploy.name, version)
      except Exception, e:
        logger.error("Failed to checkout: {}".format(str(e)))
        break

      changed[i] = True

    try:
      if all(changed):
        return True

      print("Rolling back checkout")
      for i, ((server, module), (deploy_name, version)) in enumerate(previous):
        if not changed[i]:
          continue

        print("Reverting back to  module {} (version {}-{}) on {}".format(module.name, deploy_name, version, server))

        try:
          module.checkout(server, deploy_name, version)
        except Exception, e:
          logger.error("Failed to rollback: {}".format(str(e)))

        changed[i] = False

      if any(changed):
        print "Could not rollback all changes!!!"

      return False
    finally:
      # run as much as possible and log errors
      for i, ((server, module), _) in enumerate(previous):
        if "after_checkout" in module.config:
          print "Triggering", module.name, "{after_checkout} on", server
          code = server.pretty_run(module.config.get("after_checkout"))
          if code != 0:
            logger.error("before_checkout: non-zero exit status")
