
from .base import ICommand

from .check import CheckCommand
from .checkout import CheckoutCommand
from .deploy import DeployCommand
from .help import HelpCommand
from .setup import SetupCommand
from .update import UpdateCommand
from .inspect import InspectCommand

all_commands = [
  CheckCommand,
  CheckoutCommand,
  DeployCommand,
  HelpCommand,
  SetupCommand,
  UpdateCommand,
  InspectCommand,
]

__all__ = ["all_commands"]
