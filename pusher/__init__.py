import sys
import os
import logging
import getopt

logger = logging.getLogger(__name__)

from .environment import create_env
from .commands import all_commands

def exit_usage(env):
  print("Usage: pusher <command>")
  print("General options:");
  print("-c <config>      : Specify another configuration file than default")
  print("-l <level>       : Specify logging level, one of ERROR, WARNING, INFO, DEBUG")
  print("-D <key>=<value> : Perform a temporary override of a configuration value")
  print("")
  for name, command in sorted(env.list_commands().items()):
    print "  {:25}: {}".format(name, command.short)
  sys.exit(1)

def entry():
  """
  Locate pusher.yaml in the current working directory and bootstrap a interactive deploy environment.
  """
  import yaml
  import json

  opts = {
    "config": ["pusher.yaml", "pusher.json"]
  }

  try:
    getopts, args = getopt.gnu_getopt(sys.argv[1:], "c:l:D:")
  except getopt.GetoptError, e:
    print >> sys.stderr, "Option parsing failed: " + str(e)
    sys.exit(1)

  for (o, v) in getopts:
    if o == "-c": opts["config"] = [v]
    if o == "-l": opts["log_level"] = v
    if o == "-D":
      if "=" not in v:
        opts[v] = True
      else:
        key, val = v.split("=", 1)
        opts[key] = val

  config_paths = opts["config"]
  config_path  = None
  config_dict  = None

  for conf in config_paths:
    path = os.path.join(os.getcwd(), conf)

    if not os.path.isfile(path):
      continue

    try:
      if conf.endswith(".yaml"):
        config_dict = yaml.load(open(path))
      elif conf.endswith(".json"):
        config_dict = json.load(open(path))
      else:
        print >> sys.stderr, "Unsupported file extension: {}".format(conf)
        sys.exit(1)
    except Exception, e:
      print >> sys.stderr, "Failed to open configuration {}: {}".format(conf, str(e))
      sys.exit(1)

    config_path = path
    break

  if not config_dict:
    print >> sys.stderr, "No configuration found: {}".format(", ".join(config_paths))
    sys.exit(1)

  root = os.path.dirname(config_path)

  try:
    env = create_env(root, config_dict, opts);
  except RuntimeError, e:
    print >> sys.stderr, str(e)
    sys.exit(1);

  log_level = env.config.get("log_level", "INFO")

  if not hasattr(logging, log_level):
    print >> sys.stderr, "no such log level: " + log_level
    sys.exit(1);

  f="%(asctime)s - %(name)-30s - %(levelname)-7s - %(message)s"
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
