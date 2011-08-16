import sys
import os
import logging

logger = logging.getLogger(__name__)

from zope.interface import Interface, Attribute

def check_stage(env, stage):
  if not env.contains(stage):
    print "Environment does not contain stage: " + stage

    if len(env.deploys) > 0:
      print "Available stages are:"
      for deploy in env.deploys:
        print deploy
    else:
      print "No available stages"

    print ""

    raise RuntimeError, "No such stage: " + stage

def handle_stages(env, args):
  """
  Handle a set of stage arguments, if any one is '@', replace with all available stages for that specific version.
  """
  if len(args) < 1:
    raise RuntimeError, "Number of arguments must be greater than 1"

  for a in args:
    if ":" not in a:
      raise ValueError, "invalid argument, expected <deploy>:<version>: {0}".format(a)

  args = map(lambda a: tuple(a.split(":", 1)), args)

  decl = []

  for (stage, version) in args:
    if stage == "@":
      return map(lambda s: (s, version), env.deploys.keys())
    check_stage(env, stage)
    decl.append((stage, version))

  return decl

class ICommand(Interface):
  command = Attribute("""Command string""")

  usage   = Attribute("""Usage string""")
  short   = Attribute("""Short command description""")
  docs    = Attribute("""Long documentation string""")

  def setenv(self, env):
    """
    Set the environment in which the command is running.
    """

  def validate(self, args):
    """
    Validate the arguments.
    @throws RuntimeException if arguments are invalid in some way.
    """

  def execute(self, *args):
    """
    Execute the command with the specified set of arguments.
    """
