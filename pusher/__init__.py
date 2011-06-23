import sys
import os
import logging
import getopt

logger = logging.getLogger(__name__)

from .environment import create_env
from .commands import all_commands

def exit_usage(env):
  print("Usage: pusher <command>")
  for name, command in sorted(env.list_commands().items()):
    print "  {:25}: {}".format(name, command.short)
  sys.exit(1)

def entry():
  """
  Locate pusher.yaml in the current working directory and bootstrap a interactive deploy environment.
  """
  import yaml

  opts = {
    "config": os.path.join(os.getcwd(), "pusher.yaml")
  }

  try:
    getopts, args = getopt.gnu_getopt(sys.argv[1:], "c:l:")
  except getopt.GetoptError, e:
    print >> sys.stderr, "Option parsing failed: " + str(e)
    sys.exit(1)

  for (o, v) in getopts:
    if o == "-c": opts["config"] = v
    if o == "-l": opts["log_level"] = v

  root = os.path.dirname(opts["config"])

  if not os.path.isfile(opts["config"]):
    print >> sys.stderr, "Could not find {}".format(opts["config"])
    sys.exit(1)

  config_yaml = None

  try:
    config_dict = yaml.load(open(opts["config"]))
  except Exception, e:
    print >> sys.stderr, "Failed to open configuration:", str(e)
    sys.exit(1)

  try:
    env = create_env(root, config_dict, opts);
  except RuntimeError, e:
    print >> sys.stderr, str(e)
    sys.exit(1);

  log_level = env.config.get("log_level", "INFO")

  if not hasattr(logging, log_level):
    print >> sys.stderr, "no such log level: " + log_level
    sys.exit(1);

  f="%(asctime)s - %(name)-20s - %(levelname)-7s - %(message)s"
  logging.basicConfig(level=getattr(logging, log_level), format=f)

  if len(args) < 1:
    exit_usage(env)

  command = args[0]
  args    = args[1:]

  try:
    command = env.get_command(command)
  except RuntimeError, e:
    print >> sys.stderr, "Command error: " + str(e)
    exit_usage(env)

  try:
    command.validate(args)
  except RuntimeError, e:
    print >> sys.stderr, "Invalid arguments: " + str(e)
    print >> sys.stderr, ""
    print >> sys.stderr, "Usage:", command.usage
    print >> sys.stderr, "Short:", command.short
    sys.exit(1)

  status = 0

  try:
    if command.execute(*args):
      logger.info("Command Successful")
    else:
      logger.info("Command Failed")
      status = 1
  finally:
    env.shutdown()

  sys.exit(status)
