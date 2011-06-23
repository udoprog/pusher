import os
import sys
import logging

logger = logging.getLogger(__name__)

from .components import root_objects
from .archive import Archive
from .handles import import_name
from .commands import all_commands

class PusherEnvironment(object):
  def __init__(self, root_path, config, **kw):
    """
    Initialize the environment with each specific amount of servers and modules.
    """
    self.root = root_path
    self.config = config

    self.archive = Archive(self, config.get("archive", ".archive"))
    self.archive.create()

    for klass in root_objects:
      setattr(self, klass.__group__, kw.pop(klass.__group__, {}))

    self.commands = dict()

    for klass in all_commands:
      inst = klass()
      inst.setenv(self)
      self.commands[klass.command.lower()] = inst

  def shutdown(self):
    for klass in root_objects:
      for k,v in getattr(self, klass.__group__).items():
        v.close()

  def setup(self):
    for deploy in self.deploys.values():
      deploy.setup(self)

  def contains(self, stage):
    return stage in self.deploys

  def list_commands(self):
    return self.commands

  def get_command(self, command):
    command = self.commands.get(command.lower(), None)

    if command is None:
      raise RuntimeError, "no such command: " + command

    return command

def validate_config(c):
  def check_type(k, c, vtype):
    if k not in c:
      raise RuntimeError, "{}: missing key".format(k)
    rtype = type(c[k])
    if not isinstance(c[k], vtype):
      raise RuntimeError, "{}: should be '{}' but is '{}'".format(k, vtype.__name__, rtype.__name__)

  def valid_keys(c, vtype, *keys):
    for k in keys:
      check_type(k, c, vtype)

  def valid_component(c, klass):
    if type(c) != dict:
      raise RuntimeError, "type is not 'dict'"

    for k, vtype in klass.__keys__.items():
      check_type(k, c, vtype)

  def each_key(conf, name, func):
    for i, (k, v) in enumerate(conf[name].items()):
      if v is None:
        raise RuntimeError, ("{}#{} \"{}\": value is null".format(name, i, k))

      try:
        func(v)
      except RuntimeError, e:
        raise RuntimeError, ("{}#{} \"{}\": {}".format(name, i, k, str(e)))

  valid_keys(c, dict, *[k.__group__ for k in root_objects])

  for klass in root_objects:
    each_key(c, klass.__group__, lambda c: valid_component(c, klass))

def create_components(environ, config, klass):
  comps = dict()
  for k,v in environ[klass.__group__].items():
    pconf = dict(config)
    pconf["name"] = k
    pconf.update(v)
    comp = klass(pconf)
    for attr in klass.__keys__.keys():
      val = v.get(attr, None)
      comp.set_attr(attr, val)
    comps[k] = comp
  return comps

def create_env(root, environ, opts):
  try:
    validate_config(environ)
  except RuntimeError, e:
    raise RuntimeError, "Invalid schema: "+ str(e)

  config = dict()

  if "config" in environ:
    config.update(environ["config"])

  if "handles" in config:
    for name in config.get("handles"):
      import_name(name)

  config.update(os.environ)

  config["root"] = root
  config["cwd"] = os.getcwd()

  config.update(opts)
  cache = dict(config)

  for k in config:
    if isinstance(config[k], basestring):
      config[k] = config[k].format(**cache)

  objects = dict()
  
  for klass in root_objects:
    objects[klass.__group__] = create_components(environ, config, klass)

  env = PusherEnvironment(root, config, **objects)

  try:
    env.setup()
  except RuntimeError, e:
    raise RuntimeError, "Invalid environment: {}".format(str(e))

  return env
