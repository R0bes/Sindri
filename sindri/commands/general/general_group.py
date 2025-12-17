"""General command group."""

from sindri.commands.command import Command
from sindri.commands.general.commands import (
    InstallCommand,
    SetupCommand,
)
from sindri.commands.group import CommandGroup


class GeneralGroup(CommandGroup):
    """General command group."""

    def __init__(self):
        super().__init__(
            group_id="general",
            title="General",
            description="General project commands",
            order=1,
        )
        self._command_list: list[Command] = []
        self._initialize_commands()

    def _initialize_commands(self) -> None:
        """Initialize commands for this group."""
        self._command_list = [
            SetupCommand(),
            InstallCommand(),
        ]

    def get_commands(self) -> list[Command]:
        """Get all commands in this group."""
        return self._command_list
