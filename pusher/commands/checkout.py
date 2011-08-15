import sys
import os
import logging

logger = logging.getLogger(__name__)

from .base import ICommand
from .base import handle_stages
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
    if len(args) < 1:
      raise RuntimeError, "Number of arguments must be greater than zero"

    args = map(lambda a: tuple(a.split(":", 1)), args)
    return handle_stages(self.env, args)

  def execute(self, *stages):
    all_ok = True

    for (stage, version) in stages:
      deploy = self.env.deploys.get(stage, None)

      for server in deploy.servers:
        for module in deploy.modules:
          try:
            module.check(server)
          except Exception, e:
            print "Bad server {0}: {1}".format(server, str(e))
            all_ok = False

    if not all_ok:
      return False

    previous = list()
    changed = list()

    for (stage, version) in stages:
      deploy = self.env.deploys.get(stage, None)

      print "Downloading rollback states"

      for server in deploy.servers:
        for module in deploy.modules:
          previous.append(((deploy, server, module), module.current(server)))
          changed.append(False)

    # run as little as possible with terminal errors
    for i, ((deploy, server, module), (current_name, current_version)) in enumerate(previous):
      if "before_checkout" in module.config:
        print "Triggering", module.name, "{before_checkout} on", server
        code = server.pretty_run(module.config.get("before_checkout"))
        if code != 0:
          print "before_checkout: non-zero exit status"
          return False

    for i, ((deploy, server, module), (current_name, current_version)) in enumerate(previous):
      name="{0} (version {1}-{2}) on {3}".format(module.name, deploy.name, version, server)

      if current_name == deploy.name and current_version == version:
        print("{0}: {1}".format(name, "Already checked out"))
        changed[i] = True
        continue

      print("{0}: {1}".format(name, "Checking out"))

      try:
        module.checkout(server, deploy.name, version)
      except Exception, e:
        import traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        logger.error("Failed to checkout: {0}".format(str(e)))
        break

      changed[i] = True

    try:
      if all(changed):
        return True

      print("Rolling back checkout")

      for i, ((deploy, server, module), (deploy_name, version)) in enumerate(previous):
        if not changed[i]:
          continue

        print("Reverting back to  module {0} (version {1}-{2}) on {3}".format(module.name, deploy_name, version, server))

        try:
          module.checkout(server, deploy_name, version)
        except Exception, e:
          logger.error("Failed to rollback: {0}".format(str(e)))

        changed[i] = False

      if any(changed):
        print "Could not rollback all changes!!!"

      return False
    finally:
      # run as much as possible and log errors
      for i, ((deploy, server, module), _) in enumerate(previous):
        if "after_checkout" in module.config:
          print "Triggering", module.name, "{after_checkout} on", server
          code = server.pretty_run(module.config.get("after_checkout"))
          if code != 0:
            logger.error("before_checkout: non-zero exit status")
