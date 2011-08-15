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
  decl = []

  for (stage, version) in args:
    if stage == "@":
      for s in env.deploys.keys():
        decl.append((s, version))
      return decl

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
