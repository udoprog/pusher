
from .base import ICommand

from .check import CheckCommand
from .checkout import CheckoutCommand
from .deploy import DeployCommand
from .help import HelpCommand
from .setup import SetupCommand
from .update import UpdateCommand

all_commands = [
  CheckCommand,
  CheckoutCommand,
  DeployCommand,
  HelpCommand,
  SetupCommand,
  UpdateCommand,
]

__all__ = ["all_commands"]
