"""PyPI command group."""

from sindri.commands.command import Command
from sindri.commands.group import CommandGroup
from sindri.commands.pypi.commands import (
    PyPIValidateCommand,
    PyPIPushCommand,
)


class PyPIGroup(CommandGroup):
    """PyPI command group for package publishing."""

    def __init__(self):
        super().__init__(
            group_id="pypi",
            title="PyPI",
            description="PyPI package publishing commands",
            order=3,
        )
        self._command_list: list[Command] = []
        self._initialize_commands()

    def _initialize_commands(self) -> None:
        """Initialize PyPI commands."""
        self._command_list = [
            PyPIValidateCommand(),
            PyPIPushCommand(),
        ]

    def get_commands(self) -> list[Command]:
        """Get all commands in this group."""
        return self._command_list

