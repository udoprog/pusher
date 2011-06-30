import os
import sys
import logging

logger = logging.getLogger(__name__)

from .components import root_objects
from .archive import Archive
from .handles import import_name
from .commands import all_commands

class config_dict:
  def __init__(self, params={}, override={}, parent=None):
    self.params = params
    self.parent = parent
    self.override = override

  def subp(self, parent):
    p = dict(parent.params)
    p.update(self.params)
    p.update(self.override)
    return config_dict(p, self.override, parent)

  def sub(self, **params):
    p = dict(self.params)
    p.update(params)
    p.update(self.override)
    return config_dict(p, self.override, self)

  def get(self, key, default=None, params=None):
    def config_format(s, params):
      if isinstance(s, list):
        return [config_format(r, params) for r in s]

      if isinstance(s, dict):
        kw = dict()
        for k, v in s.items():
          kw[k] = config_format(v, params)
        return kw

      if not isinstance(s, basestring):
        raise RuntimeError, "cannot format '{}' of type {}".format(key, str(type(s)))

      try:
        return s.format(**params)
      except KeyError, e:
        raise RuntimeError, "missing configuration key: " + str(e)

    if params is None:
      params = self.params

    if key in self.params:
      return config_format(self.params.get(key), params)

    if self.parent:
      return self.parent.get(key, default, params)

    if default is not None:
      return config_format(default, params)

    raise KeyError(key)

  def __contains__(self, key):
    if key in self.params:
      return True
    if self.parent:
      return key in self.parent
    return False

  def __iter__(self):
    for k in sorted(self.params.keys()):
      yield k

class PusherEnvironment(object):
  def __init__(self, root_path, config):
    """
    Initialize the environment with each specific amount of servers and modules.
    """
    self.root = root_path
    self.config = config

    self.archive = Archive(self, config.get("archive", ".archive"))
    self.archive.create()

    self.commands = dict()

    for klass in all_commands:
      inst = klass()
      inst.setenv(self)
      self.commands[klass.command.lower()] = inst

  def run(self, command):
    print "Running: {}".format(command)
    exitcode = os.system(command)

    if exitcode != 0:
      raise RuntimeError, "non-zero exitcode: {}".format(exitcode)

    return exitcode

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

def validate_config(environ, config):
  ignore = set([dict, list, tuple])

  def check_type(k, environ, vtype):
    if k not in environ:
      vv = vtype()
    else:
      vv = environ.get(k)
    rtype = type(vv)
    if not isinstance(vv, vtype):
      raise RuntimeError, "{}: should be '{}' but is '{}'".format(k, vtype.__name__, rtype.__name__)

  def valid_component(environ, klass):
    for k, vtype in klass.__keys__.items():
      check_type(k, environ, vtype)

    sub = {}

    for k, v in environ.items():
      if type(v) in ignore:
        continue
      sub[k] = v

    cc = config.sub(**sub)

    for k, vt in klass.__config_keys__.items():
      try:
        v = cc.get(k)
      except KeyError, e:
        raise RuntimeError, "missing required config key: {}".format(k)

      if not isinstance(v, vt):
        raise RuntimeError, "config key: {}: expected type {} but is {}".format(k, vt, v)

  def each_key(environ, name, func):
    if name not in environ:
      environ[name] = dict()
      return

    for i, (k, v) in enumerate(environ.get(name).items()):
      if v is None:
        raise RuntimeError, ("{}#{} \"{}\": value is null".format(name, i, k))

      if type(v) != dict:
        raise RuntimeError, "type is not 'dict'"

      try:
        func(v)
      except RuntimeError, e:
        raise RuntimeError, ("{}#{} \"{}\": {}".format(name, i, k, str(e)))

  for k in root_objects:
    check_type(k.__group__, environ, dict)

  for klass in root_objects:
    try:
      each_key(environ, klass.__group__, lambda environ: valid_component(environ, klass))
    except RuntimeError, e:
      raise RuntimeError, "root: {}: {}".format(klass.__group__, str(e))

def create_components(env, environ, klass):
  ignore = set([dict, list, tuple])

  comps = list()
  for k,v in environ[klass.__group__].items():
    sub = dict(name=k)
    sub.update(v)
    comps.append(klass(env.config.sub(**sub)))
  return comps

def create_env(root, environ, opts):
  config = dict(environ)

  if "config" in environ:
    config.update(environ["config"])

  if "handles" in config:
    for name in config.get("handles"):
      import_name(name)

  config["root"] = root
  config["cwd"]  = os.getcwd()

  config = config_dict(config, opts)

  try:
    validate_config(environ, config)
  except RuntimeError, e:
    raise RuntimeError, "Invalid schema: "+ str(e)

  env = PusherEnvironment(root, config)
  
  for klass in root_objects:
    comps = create_components(env, environ, klass)
    m = dict([(c.name, c) for c in comps])
    setattr(env, klass.__group__, m)

  try:
    env.setup()
  except RuntimeError, e:
    raise RuntimeError, "Invalid environment: {}".format(str(e))

  return env
